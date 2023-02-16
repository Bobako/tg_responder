import asyncio
import copy
import datetime
import os
import re

import telethon
from telethon import TelegramClient
from telethon import functions, types

from app.config import config
from app.models import Account, Chain, Message, ChainUsage
from app import db


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
            if db.session.query(Account).filter(Account.phone == phone).first():
                raise Exception("уже добавлен")

            tg_session_path = os.path.abspath(config["TELETHON"]["sessions_path"]) + "/" + phone + ".session"
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
CHAIN_STATUSES = {}
PENDING_USAGES = {}


class Worker:
    keep_alive = True

    def __init__(self, account_id):
        PENDING_USAGES[account_id] = []
        CHAIN_STATUSES[account_id] = {}
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
                with open(config["TELETHON"]["logs"], "a", errors="ignore") as file:
                    file.write(f"{datetime.datetime.now()}: {self.account} - Telegram internal error\n")
                return

            statuses = self.get_chain_status(sent_from)
            if statuses["active"]:
                statuses["last_message"] = event.message
            chains = db.session.query(Chain).filter(Chain.account_id == self.account.id).filter(
                Chain.turned_on == True).all()
            default = False
            try:
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
            except Exception as ex:
                remove_unfinished_chain_traces(self.account.id)
                with open(config["TELETHON"]["logs"], "a", errors="ignore") as file:
                    file.write(f"{datetime.datetime.now()}: {self.client} - {ex} во время работы\n")

    async def run(self):
        while self.keep_alive:
            self.session.refresh(self.account)
            if self.account.turned_on:
                if await self.is_client_working():
                    try:
                        await self.client.run_until_disconnected()
                    except Exception as ex:
                        with open(config["TELETHON"]["logs"], "a", errors="ignore") as file:
                            file.write(f"{datetime.datetime.now()}: {self.client} - {ex} во время работы\n")

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
        statuses = self.get_chain_status(sent_from)

        if statuses["active"]:
            if chain.in_ignore:
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

        PENDING_USAGES[self.account.id].append([chain.id, sent_from])

        db.session.commit()
        self.get_chain_status(sent_from)["active"].append(chain)
        messages = db.session.query(Message).filter(Message.chain_id == chain.id).order_by(Message.number.asc()).all()
        for message in messages:
            await asyncio.sleep(message.delay_seconds)
            await self.client.send_read_acknowledge(user_entity, tg_message)

            if message_to_respond := self.get_chain_status(sent_from)["last_message"]:
                await self.client.send_read_acknowledge(user_entity, message_to_respond)
                self.get_chain_status(sent_from)["last_message"] = None

            action = ["typing", "photo", "record-audio", "record-round", "document", "video", "audio", "location"][
                message.type]
            async with self.client.action(user_entity, action):
                await asyncio.sleep(3)
                if message.type == 0:
                    await self.client.send_message(user_entity, message.text.replace("\\n", "\n"))
                else:
                    if message.type != 7:
                        await self.client.send_file(user_entity, message.content_path,
                                                    caption=message.text.replace("\\n", "\n"),
                                                    voice_note=(message.type == 2),
                                                    video_note=(message.type == 3),
                                                    ttl=message.ttl)
                    else:
                        await self.client(functions.messages.SendMediaRequest(
                            peer=user_entity,
                            media=types.InputMediaGeoPoint(
                                types.InputGeoPoint(
                                    lat=message.latitude if message.latitude else 0,
                                    long=message.longitude if message.longitude else 0
                                )),
                            message=''
                        ))

        statuses = self.get_chain_status(sent_from)
        statuses["active"].pop(statuses["active"].index(chain))
        PENDING_USAGES[self.account.id].pop(PENDING_USAGES[self.account.id].index([chain.id, sent_from]))
        return True

    async def connect(self):
        try:
            if not self.client.is_connected():
                await self.client.connect()
            await self.client.sign_in()
        except Exception as ex:
            with open(config["TELETHON"]["logs"], "a", errors="ignore") as file:
                file.write(f"{datetime.datetime.now()}: {ex} при попытке запуска/перезапуска {self.account}\n")
            self.account.status = -1
            db.session.commit()
            return False
        else:
            # with open(config["TELETHON"]["logs"], "a") as file:
            #    file.write(f"{datetime.datetime.now()}: инициализирован {self.account}\n")
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
        if self.account.id not in CHAIN_STATUSES:
            CHAIN_STATUSES[self.account.id] = {}
        default_status = {"active": [], "responded": False, "last_message": None}
        if to_user_id not in CHAIN_STATUSES[self.account.id]:
            CHAIN_STATUSES[self.account.id][to_user_id] = copy.deepcopy(default_status)
        return CHAIN_STATUSES[self.account.id][to_user_id]


def init_workers(loop):  # on app init start in other thread
    asyncio.set_event_loop(loop)
    accounts = db.session.query(Account).all()
    for account in accounts:
        worker = Worker(account.id)
        WORKERS[account.id] = worker
        loop.create_task(worker.run())
    loop.create_task(prevent_loop_stop(loop))
    loop.run_forever()


async def prevent_loop_stop(loop):
    while True:
        await asyncio.sleep(int(config["TELETHON"]["time"]))
        for worker in WORKERS.values():
            if worker.account.turned_on:
                loop.create_task(update_worker_status(worker))


async def update_worker_status(worker: Worker):
    status = -1
    try:
        if (await worker.client.get_me()):
            status = 1
    except Exception:
        pass
    if status == -1 and worker.account.status == 1:
        with open(config["TELETHON"]["logs"], "a", errors="ignore") as file:
            file.write(f"{datetime.datetime.now()}: {worker.account} был отключен по причине 'выхода с устройства' (так же может быть вызвано потерей связи)\n")
    worker.set_status(status)


def add_worker(account_id, loop):  # while app running -> in routes
    account = db.session.query(Account).filter(Account.id == account_id).one()  # sheet
    asyncio.set_event_loop(loop)
    worker = Worker(account.id)
    WORKERS[account.id] = worker
    loop.create_task(worker.run())


async def kill_worker(account_id):  # to delete
    remove_unfinished_chain_traces(account_id)
    WORKERS[account_id].keep_alive = False
    await WORKERS[account_id].client.disconnect()
    WORKERS.pop(account_id)


async def stop_worker(account_id):
    remove_unfinished_chain_traces(account_id)
    await WORKERS[account_id].client.disconnect()


def remove_unfinished_chain_traces(account_id):
    pending_usages = PENDING_USAGES[account_id]
    while pending_usages:
        pending_usage = pending_usages.pop(0)
        chain_id, sent_from = pending_usage
        last_usage = db.session.query(ChainUsage).filter(ChainUsage.chain_id == chain_id).filter(
            ChainUsage.chat_id == sent_from).first()
        db.session.delete(last_usage)
    db.session.commit()
    for chain in CHAIN_STATUSES[account_id].values():
        chain["active"] = []


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
