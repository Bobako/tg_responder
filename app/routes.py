import asyncio

from flask import render_template, request

from app import flask_app, config
from app import db
from app.models import Account, Chain, Message
from app.bot import request_code, auth, add_sessions, add_worker, kill_worker, stop_worker
from app import forms_handler, database_shortcuts
from app import loop


@flask_app.route("/")
def index():
    groups = []
    for i in range(12):
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
        elif "delete_derived_chains" in form:
            chain_ids = form.pop("delete_derived_chains")["cids"]
            if chain_ids:
                chain_ids = map(int, chain_ids.split("-"))
                database_shortcuts.delete_derived(db.session, chain_ids, list(form.keys()))
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
                           account_id=account_id,
                           templates=templates)


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
            loop.call_soon_threadsafe(add_worker, account.id, loop)

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
        if class_ == Chain:
            if not obj.account_id:
                [db.session.delete(obj) for obj in db.session.query(Chain).filter(Chain.derived_from == id_).all()]
        db.session.delete(obj)
    db.session.commit()
    return ""


@flask_app.route("/api/move_account", methods=["post"])
def api_move_account():
    form = request.form
    form = forms_handler.parse_forms(form)
    number = 0
    group_number = 0
    for account_id, account_group_number in form.items():
        account_group_number = account_group_number["group_number"]
        if account_group_number != group_number:
            number = 0
            group_number = account_group_number
        account = db.session.query(Account).filter(Account.id == account_id).one()
        account.number = number
        account.group_number = group_number
        number += 1
    db.session.commit()

    return "ok"


@flask_app.route("/api/new_chain")
def api_new_chain():
    account_id = request.args.get("account_id")
    if account_id == 0:
        account_id = None
    chain = Chain(name="Новая цепочка", keywords="", turned_on=True, pause_seconds=0, for_group=False, self_ignore=True,
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
    cids = request.args.get("cids", "")
    action = request.args.get("action", "share")
    accounts = db.session.query(Account).all()
    return render_template("sharePopUp.html", accounts=accounts, cids=cids, action=action)


@flask_app.route("/api/add_sessions")
def api_add_session_files():
    group_number = request.args.get("group_number")
    response = asyncio.run(add_sessions(group_number, loop))
    return response


def link_keep_alive_placeholder():
    @flask_app.route("/flaskwebgui-keep-server-alive")
    def keep_alive_placeholder():
        return "ok *keep alive placeholder*"


if not bool(int(config["FLASK"]["app"])):
    link_keep_alive_placeholder()
