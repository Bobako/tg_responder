import asyncio
import datetime
import os
import re

import telethon
from telethon import TelegramClient

from app.config import config
from app.models import Account

from threading import Lock

lock = Lock()


async def request_code(phone):
    client = TelegramClient(config["TELETHON"]["sessions_path"] + phone,
                            config["TELETHON"]["id"], config["TELETHON"]["hash"])
    await client.connect()
    await client.send_code_request(phone)


async def auth(phone, code, password):
    client = TelegramClient(config["TELETHON"]["sessions_path"] + phone,
                            config["TELETHON"]["id"], config["TELETHON"]["hash"])
    await client.connect()
    await client.send_code_request(phone)
    try:
        await client.sign_in(code=code)
    except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
        await client.sign_in(password=password)
    if await client.is_user_authorized():
        me = (await client.get_me()).to_dict()
        first_name = me['first_name']
        last_name = me['last_name'] if me['last_name'] else ''
        contact = '@' + me['username'] if me['username'] else '+' + me['phone']
        user_repr = f"{first_name} {last_name} ({contact})"
        await client.disconnect()
        return user_repr
    else:
        raise Exception("Can not authorize")


async def add_sessions(session, group_number):
    files = os.listdir(config["TELETHON"]["sessions_path"])
    sessions = []
    for file in files:
        if re.match("""[0-9]+\.session$""", file):
            sessions.append(file)
    success = 0
    msg = ""
    number = len(session.query(Account).filter(Account.group_number == group_number).all())
    for session_file in sessions:
        client = TelegramClient(config["TELETHON"]["sessions_path"] + session_file, config["TELETHON"]["id"],
                                config["TELETHON"]["hash"])
        try:
            await client.connect()
            await client.sign_in()
            me = (await client.get_me()).to_dict()
            if session.query(Account).filter(Account.phone == me["phone"]).first():
                raise Exception("уже добавлен")
            first_name = me['first_name']
            last_name = me['last_name'] if me['last_name'] else ''
            contact = '@' + me['username'] if me['username'] else '+' + me['phone']
            user_repr = f"{first_name} {last_name} ({contact})"
            await client.disconnect()
        except Exception as ex:
            msg += f"{session_file}: {ex}<br>"
        else:
            print(user_repr)
            session.add(Account(phone=me["phone"], user_repr=user_repr, turned_on=True, group_number=group_number,
                                number=number, status=0))
            number += 1
            success += 1
    session.commit()
    msg = f"Аккаунтов добавлено: {success}<br>{msg}"
    return msg


WORKERS = {}


class Worker:
    keep_alive = True
    client = None

    def __init__(self, session, account):
        self.session = session
        self.account = account
        self.account.status = 0
        self.session.commit()

    async def run(self):
        while self.keep_alive:
            self.session.refresh(self.account)
            if self.account.turned_on:
                if not self.client:
                    pass  # TODO
            else:
                await asyncio.sleep(1)

    async def connect_loop(self):
        while self.keep_alive:
            try:
                client = TelegramClient(config["TELETHON"]["sessions_path"] + self.account.phone,
                                        config["TELETHON"]["id"],
                                        config["TELETHON"]["hash"])
                await client.connect()
                await client.sign_in()
            except Exception as ex:
                with open(config["TELETHON"]["logs"], "a") as file:
                    file.write(f"{datetime.datetime.now()}: {ex} при попытке инициализации {self.account}")
                self.account.status = -1
                self.session.commit()
            else:
                with open(config["TELETHON"]["logs"], "a") as file:
                    file.write(f"{datetime.datetime.now()}: инициализирован {self.account}")
                self.account.status = 1
                self.session.commit()
                break


def init_workers(session, loop):  # on app init start in other thread
    asyncio.set_event_loop(loop)
    accounts = session.query(Account).all()
    for account in accounts:
        worker = Worker(session, account)
        WORKERS[account.id] = worker
        loop.create_task(worker.run())
    loop.run_forever()


def add_worker(session, account, loop):  # while app running
    worker = Worker(session, account)
    WORKERS[account.id] = worker
    loop.call_soon_threadsafe(worker.run())


def stop_worker(account_id):
    with lock:
        WORKERS[account_id].keep_alive = False
