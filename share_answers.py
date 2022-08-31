import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

import base_handler

class ApplicationShareAnswer(tk.Frame):
    def __init__(self,main = None, user_id = None, parent = None):
        super().__init__()
        self.main = main
        self.answers = base_handler.get_answers_by_user_id(user_id)
        self.user_id = user_id
        self.parent = parent
        self.cb_values = []
        self.pads = {'padx': 10, 'pady': 10}
        for i in range(len(self.answers)):
            self.cb_values.append(tk.BooleanVar(self.main, False))

        self.share_options = ['Выбрать аккаунт']

        self.create_widgets()

    def create_widgets(self):
        self.name_label = tk.Label(self.main, text = f"Отметьте цепочки для копирования:")
        self.name_label.grid(row = 0, column = 0, **self.pads)

        for i, answer in enumerate(self.answers):
            value = self.cb_values[i]
            answer_cb = tk.Checkbutton(self.main, text = answer.name, onvalue = True, offvalue = False, variable = value)

            answer_cb.grid(row = 1+i, column = 0, sticky = tk.W, padx = 30)


        self.share_label = tk.Label(self.main, text = "Выберите аккаунт для копированя цепочек")
        self.share_label.grid(row=len(self.answers)+2, column=0, **self.pads)

        users = base_handler.get_users()
        self.share_options += [user.user_str for user in users if user.id != self.user_id]
        self.share_option_var = tk.StringVar(self.main, self.share_options[0])
        self.share_menu = ttk.OptionMenu(self.main, self.share_option_var, self.share_options[0],
                                         *self.share_options)
        self.share_menu.grid(row=len(self.answers)+2, column=1, **self.pads)

        self.share_answer_button = tk.Button(self.main, text = "Скопировать")
        self.share_answer_button.grid(row=len(self.answers)+3, column=0, **self.pads)
        self.share_answer_button.bind("<Button-1>", self.share_answer)

        self.delete_button = tk.Button(self.main, text="Удалить")
        self.delete_button.grid(row=len(self.answers) + 3, column=1, **self.pads)
        self.delete_button.bind("<Button-1>", self.delete_answers)

        self.error_label = tk.Label(self.main, text="", fg="red")
        self.error_label.grid(row=len(self.answers)+4, column=0, **self.pads)

    def delete_answers(self, *args):
        answers_to_delete = []
        for i, value in enumerate(self.cb_values):
            if value.get():
                answers_to_delete.append(self.answers[i].id)

        if not answers_to_delete:
            self.print_error("Не выбрано не одной цепочки")
            return

        response = mb.askyesno('Удаление', 'Удалить цепочки?')
        if response:
            for answer_id in answers_to_delete:
                base_handler.remove_answer(answer_id)
        self.parent.update_option_menu()
        self.print_success("Цепочки удалена")

    def share_answer(self, *args):
        user_str = self.share_option_var.get()
        if user_str == 'Выбрать аккаунт':
            self.print_error("Аккаунт не выбран")
            return

        share_with_id = base_handler.get_user_by_user_str(user_str).id

        answers_to_share = []
        for i, value in enumerate(self.cb_values):
            if value.get():
                answers_to_share.append(self.answers[i])

        if not answers_to_share:
            self.print_error("Не выбрано не одной цепочки")
            return

        failed = []
        for answer in answers_to_share:
            if base_handler.get_answer_by_name(answer.name, share_with_id):
                failed.append(answer.name)
            else:
                base_handler.share_answer(answer, share_with_id)

        if failed:
            self.print_error(f"Не были скопированы цепочки {', '.join(failed)}, так как цепочки с этими именами уже существуют на этом аккаунте")
        else:
            self.print_success('Цепочки скопированы')

    def print_error(self, text):
        self.error_label["fg"] = "red"
        self.error_label["text"] = text

    def print_success(self, text):
        self.error_label["fg"] = "green"
        self.error_label["text"] = text

def run():
    root = tk.Tk()
    root.title("Настройки автоответчика")
    root_app = ApplicationShareAnswer(None,1,1)
    root_app.mainloop()

if __name__ == '__main__':
    run()