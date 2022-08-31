import tkinter as tk
import asyncio

import telethon
from telethon.sync import TelegramClient

import settings
import base_handler
from base_handler import User, Answer, Message
import bot_async as bot


class ApplicationAddAccount(tk.Frame):
    def __init__(self, main, root_login):
        super().__init__()
        self.main = main
        self.root_login = root_login
        self.last_client = None

        self.contact_label = tk.Label(self.main, text="Введите номер телефона:")
        self.contact_entry = tk.Entry(self.main)

        self.password_label = tk.Label(self.main, text="Введите пароль (если подключена двухфакторная верификация)")
        self.password_entry = tk.Entry(self.main)


        self.conf_label = tk.Label(self.main, text="Введите код подтверждения:")
        self.conf_code_entry = tk.Entry(self.main)
        self.add_account_button = tk.Button(self.main, text="Получить код подтверждения")
        self.add_account_button.bind("<Button-1>", self.request_code)

        self.error_label = tk.Label(self.main, text="", fg="red")

        widgets = [self.contact_label, self.contact_entry, self.password_label,
                   self.password_entry, self.conf_label, self.conf_code_entry, self.add_account_button,
                   self.error_label]

        for i in range(len(widgets)):
            widgets[i].grid(row=i, column=0, padx=100, pady=10)

    def print_error(self, text):
        self.error_label["fg"] = "red"
        self.error_label["text"] = text

    def print_success(self, text):
        self.error_label["fg"] = "green"
        self.error_label["text"] = text

    def request_code(self,event,result = None):
        if not result:
            phone = self.contact_entry.get()
            if not phone:
                self.print_error("Не указан номер")
                return

            phones = [user.contact for user in base_handler.get_users()]
            if phone in phones:
                self.print_error("Этот аккаунт уже добавлен")
                return

            loop = asyncio.get_running_loop()
            loop.create_task(bot.request_code(phone,self))
            return
        status, client = result
        if status != 'sent':
            self.print_error(status)
            return

        self.add_account_button.bind("<Button-1>", self.add_account)
        self.add_account_button["text"] = "Добавить аккаунт"
        self.last_client = client
        self.print_success("Код отправлен")

    def add_account(self, event, user_str = None):
        if not user_str:
            conf_code = self.conf_code_entry.get()
            password = self.password_entry.get()

            if not conf_code:
                self.print_error("Не указан код подтверждения")
                return

            loop = asyncio.get_running_loop()
            loop.create_task(bot.add_account(conf_code, password, self.last_client, self))
            return

        phone = self.contact_entry.get()
        conf_code = self.conf_code_entry.get()

        base_handler.add_user(phone, True, user_str)
        self.print_success("Аккаунт добавлен")
        if self.root_login:
            self.root_login.update_accounts()
        self.add_account_button.bind("<Button-1>", self.request_code)
        self.add_account_button["text"] = "Получить код"


def run():
    root_add_account = tk.Tk()
    root_app = ApplicationAddAccount(root_add_account, None)
    root_app.mainloop()


if __name__ == "__main__":
    run()
