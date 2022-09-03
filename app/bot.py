import telethon
from telethon import TelegramClient

from app.config import config


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
