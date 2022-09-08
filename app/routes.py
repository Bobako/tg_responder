import asyncio
import copy
from threading import Lock

from flask import render_template, request

from app import flask_app
from app import db
from app.models import Account, Chain, Message
from app.bot import request_code, auth, add_sessions, add_worker, kill_worker, stop_worker
from app import forms_handler, database_shortcuts
from app import loop

lock = Lock()


@flask_app.route("/")
def index():
    groups = []
    for i in range(4):
        if group := db.session.query(Account).filter(
                Account.group_number == i).order_by(Account.number.asc()).all():
            groups.append(group)
    if not groups:
        groups = [[]]
    return render_template("index_page.html", groups=groups, add_button=len(groups) != 4,
                           status_titles={-1: "Не удалось подключиться", 0: "Отключен", 1: "Активен"})


@flask_app.route("/add_account")
def add_account():
    return render_template("add_account.html")


@flask_app.route("/chains", methods=["GET", "POST"])
def chains():
    account_id = request.args.get("account_id", 0)
    templates = int(account_id) == 0
    page_name = ("Цепочки сообщений", "Шаблоны")[templates]
    chain_id = 0
    if request.method == "POST":
        form = forms_handler.parse_forms(request.form, ["chain:for_group", "chain:self_ignore", "chain:in_ignore",
                                                        "chain:turned_on"])
        if "share_chains" in form:
            chain_ids = form.pop("share_chains")["cids"]

            if chain_ids:
                chain_ids = map(int, chain_ids.split("-"))
                database_shortcuts.share_chains(db.session, chain_ids, list(form.keys()))
        else:
            chain_dict = form.pop("chain")
            chain_id = chain_dict.pop("id")
            chain_obj = db.session.query(Chain).filter(Chain.id == chain_id).one()
            chain_obj.update(**chain_dict)
            for i, message in enumerate(form.values()):
                message["chain_id"] = chain_id
                message["number"] = i
            forms_handler.update_objs(db.session, form, Message)
            db.session.commit()
    chains_ = db.session.query(Chain).filter(Chain.account_id == account_id).all()
    return render_template("chains.html",
                           chain_id=chain_id,
                           page_name=page_name,
                           chains=chains_,
                           account_id=account_id)


@flask_app.route("/api/get_chain")
def api_get_chain():
    id_ = request.args.get("id")
    chain = db.session.query(Chain).filter(Chain.id == id_).one()
    messages = db.session.query(Message).filter(Message.chain_id == id_).order_by(Message.number.asc()).all()
    return render_template("chain.html",
                           chain=chain,
                           messages=messages)


@flask_app.route("/api/request_code")
def api_request_code():
    phone = request.args.get("phone")
    try:
        asyncio.run(request_code(phone))
    except Exception as ex:
        return str(ex)
    else:
        return "Код отправлен"


@flask_app.route("/api/auth")
def api_auth():
    phone = request.args.get("phone")
    code = request.args.get("code")
    password = request.args.get("password")
    group_number = request.args.get("group_number")

    try:
        user_repr = asyncio.run(auth(phone, code, password))
    except Exception as ex:
        return str(ex)
    else:
        if not db.session.query(Account).filter(Account.phone == phone).first():
            number = len(db.session.query(Account).filter(Account.group_number == group_number).all())
            account = Account(phone=phone, user_repr=user_repr, turned_on=True,
                              group_number=group_number, number=number, status=0)
            db.session.add(account)
            db.session.commit()
            loop.call_soon_threadsafe(add_worker(account.id, loop))

        return "Аккаунт добавлен"


@flask_app.route("/api/account_status")
def api_check_status():
    accounts = db.session.query(Account).all()
    statuses = {}
    for account in accounts:
        statuses[account.id] = account.status
    return statuses


@flask_app.route("/api/toggle")
def api_toggle():
    ids = request.args.get("id", None)
    class_ = request.args.get("class")
    if not ids and class_:
        return ""
    ids = list(map(int, ids.split("-")))
    class_ = globals()[class_.capitalize()]
    objs = [db.session.query(class_).filter(class_.id == id_).one() for id_ in ids]
    state = not sum(map(int, [obj.turned_on for obj in objs]))
    print(state)
    with lock:
        for obj in objs:

            obj.turned_on = state
            if class_ == Account and not state:
                asyncio.run_coroutine_threadsafe(stop_worker(obj.id), loop)
            db.session.commit()
    return ""


@flask_app.route("/api/delete")
def api_delete():
    ids = request.args.get("id", )
    class_ = request.args.get("class")
    if not ids and class_:
        return ""
    ids = list(map(int, ids.split("-")))
    class_ = globals()[class_.capitalize()]
    for id_ in ids:
        if class_ == Account:
            asyncio.run_coroutine_threadsafe(kill_worker(id_), loop)
        obj = db.session.query(class_).filter(class_.id == id_).one()
        db.session.delete(obj)
    db.session.commit()
    return ""


@flask_app.route("/api/move_account")
def api_move_account():
    number = int(request.args.get("number"))
    group = int(request.args.get("group"))
    id_ = int(request.args.get("id"))
    account = db.session.query(Account).filter(Account.id == id_).one()
    old_number = account.number
    old_group = account.group_number
    account.group_number = group
    account.number = number
    # fixing shifted accounts numbers
    for account in db.session.query(Account).filter(Account.group_number == old_group).filter(
            Account.number > old_number).filter(Account.id != id_).all():
        account.number -= 1
    for account in db.session.query(Account).filter(Account.group_number == group).filter(
            Account.number >= number).filter(Account.id != id_).all():
        account.number += 1

    db.session.commit()
    return ""


@flask_app.route("/api/new_chain")
def api_new_chain():
    account_id = request.args.get("account_id")
    if account_id == 0:
        account_id = None
    chain = Chain(name="", keywords="", turned_on=True, pause_seconds=0, for_group=False, self_ignore=True,
                  in_ignore=False,
                  account_id=account_id)
    db.session.add(chain)
    db.session.flush()
    db.session.refresh(chain)
    id_ = chain.id
    db.session.commit()
    return str(id_)


@flask_app.route("/api/get_accounts_to_share")
def api_get_accounts():
    account_id = request.args.get("account_id", None)
    cids = request.args.get("cids", "")
    query = db.session.query(Account)
    if account_id:
        query = query.filter(Account.id != account_id)
    accounts = query.all()
    return render_template("sharePopUp.html", accounts=accounts, cids=cids)


@flask_app.route("/api/add_sessions")
def api_add_session_files():
    group_number = request.args.get("group_number")
    response = asyncio.run(add_sessions(group_number, loop))
    return response
