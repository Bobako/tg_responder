# Telegram enhanced responder

Программа предоставляет функционал автоответчика, с возможностью создавать цепочки сообщений, который отправятся в ответ
на пришедшее ключевое слово, отправлять любые материалы (файлы, голосовые сообщения, фото, видео, кружочки), настраивать
задержку между сообщениями. Широкие возможности для создания юзер-ботов без программирования. Поддерживает множество 
аккаунтов.

Новая версия проекта (c улучшенным визуалом и новыми функциями) лежит в [ветке dev](https://github.com/Bobako/tg_responder/tree/dev).

[Посмотреть ТЗ на проект](task.md).

Инструменты, использованные в проекте:

- Python (SQLAlchemy, Telethon, Asyncio, Tkinter)

Как потрогать проект:

1) Клонировать проект.
2) Далее, либо запускать исполняемый файл ./executables/(linux или windows)/bot_async(.exe)
3) Либо запускать исходники, для этого:
4) Нужен [python3.10](https://www.python.org/downloads/) с возможность запускать pip.
5) В папке с проектом pip install -r requirments.txt
6) Можно запускать bot_async.py
