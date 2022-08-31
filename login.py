import tkinter as tk
import asyncio
import tkinter.messagebox as mb

import base_handler
from base_handler import User, Answer, Message
from add_account import ApplicationAddAccount
from account_settings import ApplicationAccountSettings
import bot_async as bot


class ApplicationLogin(tk.Frame):
    def __init__(self, main):
        super().__init__()
        self.user_buttons = []
        self.main = main
        self.set_widgets()
        self.check_auth()

    def set_widgets(self):
        users = base_handler.get_users()
        headers_text = ["Аккаунт", "Автоответчик"]
        for i in range(len(headers_text)):
            header = tk.Label(self.main, text=headers_text[i])
            header.grid(row=0, column=i)

        self.update_accounts()

        add_user_button = tk.Button(self.main, text="Добавить аккаунт", width=25, height=1)
        add_user_button.bind("<Button-1>", lambda event, arg=self: add_account_window(event, arg))

        add_user_button.grid(row=1000, column=0, padx=100, pady=10)

        # self.run_bot_button = tk.Button(self.main, text="Запустить бота")
        # self.run_bot_button.bind("<Button-1>", self.run_bot)
        # self.run_bot_button.grid(row=len(users) + 3, column=0, padx=100, pady=10)

        self.error_label = tk.Label(self.main)
        self.error_label.grid(row=len(users) + 2, column=0, padx=100, pady=10)

    def update_accounts(self):
        for button in self.user_buttons:
            button.destroy()
        self.user_buttons = []

        users = base_handler.get_users()
        for i in range(len(users)):
            user = users[i]

            delete_button = tk.Button(self.main, text="Удалить")
            delete_button.bind("<Button-1>", lambda event, arg=user.id: self.delete_account(event, arg))
            delete_button.grid(row=i + 1, column=3, padx=5)
            self.user_buttons.append(delete_button)

            button = tk.Button(self.main, text=user.user_str, width=25, height=1)
            button.grid(row=1 + i, column=0, padx=100, pady=10)
            button.bind("<Button-1>", lambda event, arg=user.id: run_account_settings(event, arg))
            self.user_buttons.append(button)

            active_button = tk.Button(self.main, text=["Выключен", "Включен"][user.active])
            self.user_buttons.append(active_button)
            active_button.grid(row=i + 1, column=1)
            active_button.bind("<Button-1>",
                               lambda event, arg=(user.contact, active_button): toggle_account(event, arg))

    def delete_account(self, event, user_id):
        response = mb.askyesno('Удаление', 'Удалить аккаунт?')
        if response:
            base_handler.remove_account(user_id)
            self.update_accounts()

    def print_error(self, text):
        self.error_label["fg"] = "red"
        self.error_label["text"] = text

    def print_success(self, text):
        self.error_label["fg"] = "green"
        self.error_label["text"] = text

    def check_auth(self):
        users = base_handler.get_users()
        loop = asyncio.get_running_loop()
        #loop.create_task(bot.is_authed(users, self))



def add_account_window(event, login_root):
    root_add_account = tk.Toplevel()
    root_add_account.title("Добавить аккаунт")
    root_app = ApplicationAddAccount(root_add_account, login_root)


def toggle_account(event, arg):
    contact, active_button = arg
    user = base_handler.get_user_by_contact(contact)
    base_handler.update_user(user.id, active=not user.active)
    active_button["text"] = ["Выключен", "Включен"][not user.active]


def run_account_settings(event, arg):
    root_account_settings = tk.Toplevel()
    root_account_settings.title("Настройки аккаунта")
    root_app = ApplicationAccountSettings(root_account_settings, arg)


def run():
    root_login = tk.Tk()
    root_login.title("Настройки автоответчика")
    root_app = ApplicationLogin(root_login)
    root_app.mainloop()


async def run_app():
    root_login = tk.Tk()
    root_login.title("Настройки автоответчика")
    root_app = ApplicationLogin(root_login)
    while True:
        await asyncio.sleep(0.1)
        root_app.update()


# get_conf_code_button.bind("<Button-1>", lambda event, arg=12: get_conf_code(event, arg))
if __name__ == "__main__":
    run()
