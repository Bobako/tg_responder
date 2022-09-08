import asyncio
import datetime
import os
import re

import telethon
from telethon import TelegramClient

from app.config import config
from app.models import Account, Chain, Message, ChainUsage
from app import db
from threading import Lock

lock = Lock()


async def request_code(phone):
    client = TelegramClient(config["TELETHON"]["sessions_path"] + phone,
                            config["TELETHON"]["id"], config["TELETHON"]["hash"])
    await client.connect()
    await client.send_code_request(phone)
    await client.disconnect()


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


async def add_sessions(group_number, loop):
    files = os.listdir(config["TELETHON"]["sessions_path"])
    sessions = []
    for file in files:
        if re.match("""[0-9]+\.session$""", file):
            sessions.append(file)
    success = 0
    msg = ""
    number = len(db.session.query(Account).filter(Account.group_number == group_number).all())
    for session_file in sessions:
        try:
            phone = session_file.replace(".session", "")
            print(phone)
            if db.session.query(Account).filter(Account.phone == phone).first():
                raise Exception("уже добавлен")

            tg_session_path = os.path.abspath(config["TELETHON"]["sessions_path"]) + "/" + phone + ".session"
            print(tg_session_path)
            client = TelegramClient(tg_session_path, config["TELETHON"]["id"],
                                    config["TELETHON"]["hash"])
            await client.connect()
            await client.sign_in()
            me = (await client.get_me()).to_dict()
            first_name = me['first_name']
            last_name = me['last_name'] if me['last_name'] else ''
            contact = '@' + me['username'] if me['username'] else '+' + me['phone']
            user_repr = f"{first_name} {last_name} ({contact})"
            await client.disconnect()
        except Exception as ex:
            msg += f"{session_file}: {ex}<br>"
        else:
            account = Account(phone=phone, user_repr=user_repr, turned_on=True, group_number=group_number,
                              number=number, status=0)
            db.session.add(account)
            db.session.commit()
            loop.call_soon_threadsafe(add_worker, account.id, loop)
            number += 1
            success += 1

    msg = f"Аккаунтов добавлено: {success}<br>{msg}"
    return msg


WORKERS = {}


class Worker:
    keep_alive = True
    chain_statuses = {}

    def __init__(self, account_id):
        self.account = db.session.query(Account).filter(Account.id == account_id).one()
        self.session = db.session
        self.account.status = 0
        tg_session_path = os.path.abspath(config["TELETHON"]["sessions_path"]) + "/" + self.account.phone + ".session"
        self.client = TelegramClient(
            tg_session_path,
            config["TELETHON"]["id"],
            config["TELETHON"]["hash"])
        self.create_handler()

    def create_handler(self):
        @self.client.on(telethon.events.NewMessage())
        async def handle_message(event):
            message = event.message.to_dict()["message"]
            msg_peer = event.message.to_dict()["peer_id"]["_"]
            group = False
            if msg_peer == "PeerUser":
                sent_from = event.message.to_dict()["peer_id"]["user_id"]
            elif msg_peer == "PeerChat":
                sent_from = event.message.to_dict()["peer_id"]["chat_id"]
                group = True
            else:
                return

            if group:
                if not event.message.to_dict()["mentioned"]:
                    return
                else:
                    dog_index = message.find('@')
                    space_index = message[dog_index:].find(' ')
                    message = message[:dog_index] + message[space_index + 1:]

            user_entity = None
            dialog = (await self.client.get_dialogs())[0]

            for _ in range(5):
                try:
                    user_entity = await self.client.get_entity(sent_from)
                except Exception:
                    try:
                        user_entity = dialog.entity
                    except Exception:
                        pass
                    else:
                        break
                else:
                    break

            if not user_entity:
                with open(config["TELETHON"]["logs"], "a") as file:
                    file.write(f"{datetime.datetime.now()}: {self.account} - Telegram internal error\n")
                return

            if self.get_chain_status(sent_from)["active"]:
                loop = asyncio.get_running_loop()
                loop.create_task(self.mark_as_read_when_read(event.message, sent_from, user_entity))

            chains = db.session.query(Chain).filter(Chain.account_id == self.account.id).filter(
                Chain.turned_on == True).all()
            default = False
            for chain in chains:
                keywords = chain.keywords.replace('*', '').split("//")
                if keywords == ['']:
                    keywords = None
                if not keywords:
                    default = True
                    continue

                if is_similar_in_list(message, keywords):
                    was_actually_send = await self.run_chain(chain, group, event.message, sent_from,
                                                             user_entity)
                    if was_actually_send:
                        return

            if default:
                for chain in chains:
                    if not chain.keywords:
                        was_actually_send = await self.run_chain(chain, group, event.message, sent_from,
                                                                 user_entity)
                        if was_actually_send:
                            return

    async def run(self):
        while self.keep_alive:
            self.session.refresh(self.account)
            if self.account.turned_on:
                if await self.is_client_working():
                    try:
                        await self.client.run_until_disconnected()
                    except Exception as ex:
                        with open(config["TELETHON"]["logs"], "a") as file:
                            file.write(f"{datetime.datetime.now()}: {ex} во время работы\n")

                else:
                    status = [-1, 1][(await self.connect())]
                    self.set_status(status)
            else:
                self.set_status(0)

            await asyncio.sleep(1)

    async def run_chain(self, chain, group, tg_message, sent_from, user_entity):
        if group != chain.for_group:
            return

        if tg_message.to_dict()['out'] and chain.self_ignore:
            return

        if self.get_chain_status(sent_from)["active"] and chain.in_ignore:
            return


        if last_usage := db.session.query(ChainUsage).filter(ChainUsage.chain_id == chain.id).filter(
                ChainUsage.chat_id == sent_from).first():
            if last_usage.usage_datetime + datetime.timedelta(seconds=chain.pause_seconds) > datetime.datetime.now():
                return

        if not last_usage:
            last_usage = ChainUsage(chain.id, sent_from)
            db.session.add(last_usage)
        else:
            last_usage.update()
        db.session.commit()

        self.get_chain_status(sent_from)["active"] = True

        messages = db.session.query(Message).filter(Message.chain_id == chain.id).order_by(Message.number.asc()).all()
        for message in messages:
            await asyncio.sleep(message.delay_seconds)
            await self.client.send_read_acknowledge(user_entity, tg_message)

            self.get_chain_status(sent_from)["responded"] = True

            action = ["typing", "photo", "record-audio", "record-round", "document", "video", "audio"][message.type]
            async with self.client.action(user_entity, action):
                await asyncio.sleep(3)
                if message.type == 0:
                    await self.client.send_message(user_entity, message.text)
                else:
                    await self.client.send_file(user_entity, message.content_path, caption=message.text,
                                                voice_note=(message.type == 2),
                                                video_note=(message.type == 3))

        self.get_chain_status(sent_from)["active"] = False
        return True

    async def connect(self):
        try:
            if not self.client.is_connected():
                await self.client.connect()
            await self.client.sign_in()
        except Exception as ex:
            with open(config["TELETHON"]["logs"], "a") as file:
                file.write(f"{datetime.datetime.now()}: {ex} при попытке запуска/перезапуска {self.account}\n")
            self.account.status = -1
            db.session.commit()
            return False
        else:
            with open(config["TELETHON"]["logs"], "a") as file:
                file.write(f"{datetime.datetime.now()}: инициализирован {self.account}\n")
            self.account.status = 1
            db.session.commit()
            return True

    async def is_client_working(self):
        if self.client.is_connected():
            return await self.client.is_user_authorized()
        return False

    def set_status(self, status):
        if self.account.status != status:
            self.account.status = status
            db.session.commit()

    def get_chain_status(self, to_user_id):
        default_status = {"active": False, "responded": False}
        if to_user_id not in self.chain_statuses:
            self.chain_statuses[to_user_id] = default_status
        return self.chain_statuses[to_user_id]

    async def mark_as_read_when_read(self, tg_message, sent_from, user_entity):
        status = self.get_chain_status(sent_from)
        status["responded"] = False
        while self.keep_alive:
            if not status["active"]:
                break
            if status["responded"]:
                break
            await asyncio.sleep(0.3)
        await self.client.send_read_acknowledge(user_entity, tg_message)


def init_workers(loop):  # on app init start in other thread
    asyncio.set_event_loop(loop)
    accounts = db.session.query(Account).all()
    for account in accounts:
        worker = Worker(account.id)
        WORKERS[account.id] = worker
        loop.create_task(worker.run())
    loop.create_task(prevent_loop_stop())
    loop.run_forever()


async def prevent_loop_stop():
    while True:
        await asyncio.sleep(60)


def add_worker(account_id, loop):  # while app running -> in routes
    account = db.session.query(Account).filter(Account.id == account_id).one()  # sheet
    asyncio.set_event_loop(loop)
    worker = Worker(account.id)
    WORKERS[account.id] = worker
    loop.create_task(worker.run())


async def kill_worker(account_id):  # to delete
    with lock:
        await WORKERS[account_id].client.disconnect()
        WORKERS[account_id].keep_alive = False
        WORKERS.pop(account_id)


async def stop_worker(account_id):
    with lock:
        await WORKERS[account_id].client.disconnect()


def is_similar(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()

    if s2 in s1:
        return True
    else:
        return False


def is_similar_in_list(s, keywords):
    for word in keywords:
        if is_similar(s, word):
            return True
    return False
