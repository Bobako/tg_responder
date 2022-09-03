import asyncio

from flask import render_template, request

from app import flask_app
from app import db
from app.models import Account
from app.bot import request_code, auth


@flask_app.route("/")
def index():
    groups = []
    for i in range(4):
        if group := db.session.query(Account).filter(
                Account.group_number == i).order_by(Account.number.asc()).all():
            groups.append(group)
    if not groups:
        groups = [[], []]
    return render_template("index_page.html", groups=groups, add_button=len(groups) != 4)


@flask_app.route("/add_account")
def add_account():
    return render_template("add_account.html")


@flask_app.route("/chains")
def chains():
    return "a"


@flask_app.route("/templates")
def templates():
    return "a"


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
            db.session.add(Account(phone=phone, user_repr=user_repr, turned_on=True,
                                   group_number=group_number, number=number))
            db.session.commit()
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
        return
    ids = list(map(int, ids.split("-")))
    # TODO
    return ""


@flask_app.route("/api/delete")
def api_delete():
    ids = request.args.get("id", )
    class_ = request.args.get("class")
    if not ids and class_:
        return
    ids = list(map(int, ids.split("-")))

    classes = {"Account"}

    return ""


@flask_app.route("/api/move_account")
def api_move_account():
    number = request.args.get("number")
    group = request.args.get("group")
    id_ = request.args.get("id")
    account = db.session.query(Account).filter(Account.id == id_).one()
    old_number = account.number
    old_group = account.group
    account.group_number = group
    account.number = number

    # fixing shifted accounts numbers
    accounts = db.session(Account).filter(Account.group_number == old_group).filter(Account.number >= old_number).all()
    for account in accounts:
        account.number -= 1

    accounts = db.session(Account).filter(Account.group_number == group).filter(Account.number > number).all()
    for account in accounts:
        account.number += 1


    db.session.commit()
    return ""