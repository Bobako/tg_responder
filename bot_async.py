import asyncio
import difflib
import time

import telethon
from telethon import TelegramClient, events

import settings
import base_handler
import login


async def run_user(user):
    async with TelegramClient(user.contact, settings.API_ID, settings.API_HASH) as client:
        print('Active', user.contact)

        @client.on(telethon.events.NewMessage())
        async def normal_handler(event):
            message = event.message.to_dict()["message"]
            msg_peer = event.message.to_dict()["peer_id"]["_"]



            group = False

            if msg_peer == "PeerUser":
                sent_from = event.message.to_dict()["peer_id"]["user_id"]
            elif msg_peer =="PeerChat":
                sent_from = event.message.to_dict()["peer_id"]["chat_id"]
                group = True
                mentioned = event.message.to_dict()["mentioned"]
            else:
                return


            user_active = base_handler.get_user(user.id).active
            if not user_active:
                return


            if group:
                if not mentioned:
                    return
                else:
                    dog_index = message.find('@')
                    space_index = message[dog_index:].find(' ')
                    message = message[:dog_index] + message[space_index + 1:]




            user_entity = None
            dialog = (await client.get_dialogs())[0]

            for _ in range(5):

                try:
                    user_entity = await client.get_entity(sent_from)
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
                print("Telegram internal error")
                return



            if base_handler.is_answer_active(user.id,sent_from):

                loop = asyncio.get_running_loop()
                loop.create_task(wait_respond_to_read(client, user_entity, event.message, user.id, sent_from))


            answers = base_handler.get_active_answers(user.id)
            default = False

            for answer in answers:
                keywords = answer.keywords.replace('*', '').split("//")
                if keywords == ['']:
                    keywords = None

                if not keywords:
                    default = True
                    continue
                if is_similar_in_list(message, keywords):
                    result = await run_answer(answer, sent_from, event.message, client, group=group, user=user, user_entity = user_entity)
                    if result:
                        return

            if default:
                for answer in answers:
                    if not answer.keywords:
                        result = await run_answer(answer, sent_from, event.message, client, group=group, user=user, user_entity = user_entity)
                        if result:
                            return


        await client.run_until_disconnected()


def get_used_dict(used):
    used_dict = {}
    if used:
        used = used.split(',')
        for i in range(len(used)):
            if used[i]:
                user_id, used_time = map(int, used[i].split(':'))
                used_dict[user_id] = used_time
    return used_dict


def get_used_str(used_dict):
    used_str = ""
    for key in list(used_dict.keys()):
        used_str += f"{key}:{used_dict[key]},"
    return used_str


async def run_answer(answer, sent_from, tg_message, client, group=False, user = None, user_entity = None):
    if group != answer.group:
        return

    if tg_message.to_dict()['out'] and answer.self_ignore:
        return

    messages = base_handler.get_messages_by_answer_id(answer.id)
    messages = base_handler.sort_messages(messages)

    if base_handler.is_answer_active(user.id, sent_from) and answer.in_ignore:
        return

    used_dict = get_used_dict(answer.used)
    if sent_from in list(used_dict.keys()):
        if not (int(time.time()) - used_dict[sent_from] > int(answer.pause)):
            #print("paused")
            return

    used_dict[int(sent_from)] = int(time.time())
    used_str = get_used_str(used_dict)
    base_handler.update_answer(answer.id, used=used_str)





    base_handler.add_active_answer(user.id, sent_from)

    for message in messages:
        await asyncio.sleep(message.delay)
        await client.send_read_acknowledge(user_entity, tg_message)
        base_handler.respond_active_answer(user.id, sent_from)
        action = ["typing", "photo", "record-audio", "record-round", "document", "video", "audio"][message.type_]
        async with client.action(user_entity, action):
            await asyncio.sleep(3)
            if message.type_ == base_handler.MSG_TYPE_TEXT:
                await client.send_message(user_entity, message.text)
            else:
                await client.send_file(user_entity, message.content_path, caption=message.text,
                                       voice_note=(message.type_ == base_handler.MSG_TYPE_AUDIO),
                                       video_note=(message.type_ == base_handler.MSG_TYPE_VIDEO))


    base_handler.remove_active_answer(user.id, sent_from)
    return True

async def wait_respond_to_read(client, user_entity, message, user_id, sent_from):

    while True:

        if not base_handler.is_answer_active(user_id, sent_from):
            break
        if base_handler.is_active_answer_respond(user_id, sent_from):
            break
        await asyncio.sleep(0.1)
    await client.send_read_acknowledge(user_entity, message)

    return



async def test():
    async with TelegramClient('+79168183093', settings.API_ID, settings.API_HASH) as client:
        await client.send_file('+79254910318', 'content/test.mp4', video_note=True)


async def is_authed(users, app):
    for user in users:
        async with TelegramClient(user.contact, settings.API_ID, settings.API_HASH) as client:
            if not await client.is_user_authorized():
                app.print_error(
                    f"{user.user_str}: ошибка при подключении - сессия была прервана, удалите аккаунт и добавьте заново")
                return


async def request_code(contact, app):
    status = 'sent'
    client = TelegramClient(contact, settings.API_ID, settings.API_HASH)
    await client.connect()
    try:
        await client.send_code_request(contact)
    except Exception as ex:
        status = ex
    app.request_code(None, (status, client))


async def add_account(conf_code, password, client, app):
    if not password:
        password = None
    await client.connect()

    try:
        await client.sign_in(code=conf_code)
    except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
        try:
            await client.sign_in(password=password)
        except Exception as ex:
            app.print_error(ex)
            return
    except Exception as ex:
        app.print_error(ex)
        return

    me = (await client.get_me())
    if me:
        me = me.to_dict()

        first_name = me['first_name']
        last_name = me['last_name'] if me['last_name'] else ''
        contact = '@' + me['username'] if me['username'] else '+' + me['phone']
        user_str = f"{first_name} {last_name} ({contact})"

    else:
        user_str = ''
    await client.disconnect()

    app.add_account(None, user_str)


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


async def main(run_app=None):
    users = base_handler.get_users()
    coros = [run_user(user) for user in users]
    if run_app:
        coros.append(run_app)

    await asyncio.gather(*coros)


if __name__ == '__main__':
    #print (is_similar_in_list('привет как дела', ['привет']))

    # asyncio.run(test())
    base_handler.clear_active_answers()
    asyncio.run(main(login.run_app()))
