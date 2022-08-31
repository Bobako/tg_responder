import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

import base_handler
from share_answers import ApplicationShareAnswer

class ApplicationAccountSettings(tk.Frame):
    def __init__(self, main, user_id):
        super().__init__()
        self.main = main
        self.user_id = user_id
        self.pads = {'padx': 10, 'pady': 10}
        self.small_pads = {'padx': 5, 'pady': 5}
        self.answers = base_handler.get_answers_by_user_id(user_id)

        self.option_var = tk.StringVar(self.main)

        self.type_options = ["Текст", "Фото", "Голосовое сообщение", "Видео-сообщение", "Документ", "Видео",
                             "Звуковой файл"]

        self.create_widgets()

    def update_option_menu(self):
        self.answers = base_handler.get_answers_by_user_id(self.user_id)
        self.answers_names = [answer.name for answer in self.answers] + ["Добавить новую"]
        self.option_menu.destroy()

        self.option_menu = ttk.OptionMenu(
            self.top_frame,
            self.option_var,
            self.answers_names[-1],
            *self.answers_names,
            command=self.option_changed)

        self.option_menu.grid(row=0, column=1, **self.pads)
        self.update_answer_entries()
        self.update_message_entries()
        self.option_changed(None)

    def create_widgets(self):
        self.top_frame = tk.Frame(self.main)

        self.answers_names = [answer.name for answer in self.answers] + ["Добавить новую"]

        self.choice_label = tk.Label(self.top_frame, text="Выберите цепочку сообщений:")
        self.choice_label.grid(row=0, column=0, **self.pads)

        self.option_menu = ttk.OptionMenu(
            self.top_frame,
            self.option_var,
            self.answers_names[0],
            *self.answers_names,
            command=self.option_changed)

        if len(self.answers_names) > 1:
            cur_answer_name = self.answers_names[0]
            self.current_answer = base_handler.get_answer_by_name(cur_answer_name, self.user_id)
            self.current_answer_id = self.current_answer.id
        else:
            self.current_answer = None
            self.current_answer_id = None

        self.option_menu.grid(row=0, column=1, **self.pads)

        left_widgets = []
        right_widgets = []

        self.answer_name_label = tk.Label(self.top_frame, text="Название цепочки:")

        left_widgets.append(self.answer_name_label)
        self.answer_name_entry = tk.Entry(self.top_frame)
        if self.current_answer:
            self.answer_name_entry.insert(tk.END, self.current_answer.name)
        right_widgets.append(self.answer_name_entry)

        self.keywords_label = tk.Label(self.top_frame, text="Фразы, активирующие цепочку:")
        left_widgets.append(self.keywords_label)
        self.keywords_entry = tk.Entry(self.top_frame)
        if self.current_answer:
            self.keywords_entry.insert(tk.END, self.current_answer.keywords)
        right_widgets.append(self.keywords_entry)

        for i in range(len(left_widgets)):
            left_widgets[i].grid(row=i + 1, column=0, **self.pads)
            right_widgets[i].grid(row=i + 1, column=1, **self.pads)

        self.top_frame.pack()

        self.msg_frame = tk.Frame(self.main)
        self.view_messages_header()
        self.view_messages(self.current_answer_id)
        self.create_message_entries()
        self.msg_frame.pack()

        confirm_frame = tk.Frame(self.main)


        self.add_message_button = tk.Button(confirm_frame, text="Добавить сообщение")
        self.add_message_button.bind("<Button-1>", self.create_message_entries)
        active_text = "Цепочка отключена"
        if self.current_answer:
            active_text = ["Цепочка отключена", "Цепочка активна"][self.current_answer.active]
        self.active_button = tk.Button(confirm_frame, text=active_text)
        self.active_button.bind("<Button-1>", self.toggle_answer)
        self.save_button = tk.Button(confirm_frame, text="Сохранить цепочку")
        self.save_button.bind("<Button-1>", self.save_answer)



        self.self_react_value = tk.BooleanVar(self.main, False)
        self.self_react_cb = tk.Checkbutton(confirm_frame, text = "Реагировать на исходящие", onvalue=True, offvalue=False,
                                         variable=self.self_react_value)
        self.self_react_cb.grid(row=1, column = 0)

        self.in_ignore_value = tk.BooleanVar(self.main, True)
        self.in_ignore_cb = tk.Checkbutton(confirm_frame, text="Игнорировать входящие", onvalue=True,
                                            offvalue=False,
                                            variable=self.in_ignore_value)
        self.in_ignore_cb.grid(row=2, column=0)

        if self.current_answer:
            self.self_react_value.set(not self.current_answer.self_ignore)
            self.in_ignore_value.set(self.current_answer.in_ignore)


        self.share_button = tk.Button(confirm_frame, text="Действия с множеством цепочек")
        self.share_button.grid(row=2, column=1)
        self.share_button.bind("<Button-1>", self.share_answers)

        self.delete_button = tk.Button(confirm_frame, text="Удалить цепочку")
        self.delete_button.bind("<Button-1>", self.delete_answer_dialog)

        self.add_message_button.grid(row=0, column=1, **self.pads)
        self.active_button.grid(row=0, column=2, **self.pads)
        self.save_button.grid(row=0, column=3, **self.pads)
        self.delete_button.grid(row=2, column=3, **self.pads)

        self.pause_label = tk.Label(confirm_frame, text="Время паузы для цепочки в секундах")
        self.pause_label.grid(row=1, column=1)

        self.grop_value = tk.BooleanVar()
        self.grop_value.set(False)
        if self.current_answer:
            self.grop_value.set(self.current_answer.group)
        self.grop_check = tk.Checkbutton(confirm_frame, text="Цепочка для чатов", onvalue=True, offvalue=False,
                                         variable=self.grop_value)
        self.grop_check.grid(row=1, column=3)
        self.pause_entry = tk.Entry(confirm_frame)
        self.pause_entry.grid(row=1, column=2)
        if self.current_answer:
            self.pause_entry.insert(0, self.current_answer.pause)
        else:
            self.pause_entry.insert(0, '0')

        confirm_frame.pack()
        self.error_label = tk.Label(self.main, text="", fg="red")
        self.error_label.pack()


    def share_answers(self, *args):
        root_share_answers = tk.Toplevel()
        root_share_answers.title("Действия с множеством цепочек")
        root_share_answers.geometry('400x200')
        root_app = ApplicationShareAnswer(root_share_answers,self.user_id,self)


    def delete_answer_dialog(self, event):

        if self.current_answer_id is None:
            self.print_error("Цепочка не выбрана")
            return

        response = mb.askyesno('Удаление', 'Удалить цепочку?')
        if response:
            base_handler.remove_answer(self.current_answer_id)
            self.update_option_menu()
            self.print_success("Цепочка удалена")

    def toggle_answer(self, event):
        active_text = "Цепочка отключена"
        if self.current_answer:
            active = not self.current_answer.active
            self.current_answer.active = active
            base_handler.update_answer(self.current_answer.id, active=active)
            active_text = ["Цепочка отключена", "Цепочка активна"][active]
            self.active_button["text"] = active_text
        else:
            self.print_error("Цепочка еще не создана")

    def update_answer_entries(self):
        self.answer_name_entry.delete(0, tk.END)
        self.keywords_entry.delete(0, tk.END)
        self.pause_entry.delete(0, tk.END)
        if self.current_answer:
            self.answer_name_entry.insert(tk.END, self.current_answer.name)
            self.keywords_entry.insert(tk.END, self.current_answer.keywords)
            self.pause_entry.insert(0, self.current_answer.pause)
        else:
            self.pause_entry.insert(0, '0')

        self.grop_value.set(False)
        if self.current_answer:
            self.grop_value.set(self.current_answer.group)

        if self.current_answer:
            active_text = ["Цепочка отключена", "Цепочка активна"][self.current_answer.active]
            self.active_button["text"] = active_text
        else:
            self.active_button["text"] = "Цепочка отключена"

        if self.current_answer:
            self.self_react_value.set(not self.current_answer.self_ignore)
            self.in_ignore_value.set(self.current_answer.in_ignore)
        else:
            self.self_react_value.set(False)
            self.in_ignore_value.set(True)


    def update_message_entries(self):
        for entry in self.message_numbers_entries + self.message_texts_entries + self.message_content_paths_entries + self.message_delays_entries + self.message_type_menues:
            entry.destroy()
        self.view_messages(self.current_answer_id)
        self.create_message_entries()

    def option_changed(self, *args):
        name = self.option_var.get()
        if name != "Добавить новую":
            self.current_answer = base_handler.get_answer_by_name(name, self.user_id)
            self.current_answer_id = self.current_answer.id
        else:
            self.current_answer = None
            self.current_answer_id = None

        self.update_answer_entries()
        self.update_message_entries()

    def view_messages_header(self):
        number_label = tk.Label(self.msg_frame, text="Порядковый номер сообщения")
        number_label.grid(row=0, column=0, **self.pads)
        number_label = tk.Label(self.msg_frame, text="Текст сообщения")
        number_label.grid(row=0, column=1, **self.pads)
        number_label = tk.Label(self.msg_frame, text="Путь к содержимому")
        number_label.grid(row=0, column=2, **self.pads)
        number_label = tk.Label(self.msg_frame, text="Задержка перед отправкой")
        number_label.grid(row=0, column=3, **self.pads)
        number_label = tk.Label(self.msg_frame, text="Тип сообщения")
        number_label.grid(row=0, column=4, **self.pads)

    def view_messages(self, answer_id=None):
        self.message_numbers_entries = []
        self.message_texts_entries = []
        self.message_content_paths_entries = []
        self.message_delays_entries = []
        self.message_type_menues = []
        self.type_option_vars = []
        if answer_id:
            messages = base_handler.sort_messages(base_handler.get_messages_by_answer_id(answer_id))
            if messages:
                for i in range(len(messages)):
                    message = messages[i]

                    number_entry = tk.Entry(self.msg_frame)
                    number_entry.insert(tk.END, str(message.number))
                    self.message_numbers_entries.append(number_entry)
                    number_entry.grid(column=0, row=i + 1, **self.small_pads)

                    text_entry = tk.Entry(self.msg_frame)
                    text_entry.insert(tk.END, str(message.text))
                    self.message_texts_entries.append(text_entry)
                    text_entry.grid(column=1, row=i + 1)

                    content_path_entry = tk.Entry(self.msg_frame)
                    content_path_entry.insert(tk.END, str(message.content_path))
                    self.message_content_paths_entries.append(content_path_entry)
                    content_path_entry.grid(column=2, row=i + 1)

                    delay_entry = tk.Entry(self.msg_frame)
                    delay_entry.insert(tk.END, str(message.delay))
                    self.message_delays_entries.append(delay_entry)
                    delay_entry.grid(column=3, row=i + 1)

                    current_option = self.type_options[message.type_]
                    type_option_var = tk.StringVar(self.msg_frame)
                    self.type_option_vars.append(type_option_var)
                    type_option_menu = ttk.OptionMenu(self.msg_frame, type_option_var, current_option,
                                                      *self.type_options)
                    self.message_type_menues.append(type_option_menu)
                    type_option_menu.grid(column=4, row=i + 1)

    def create_message_entries(self, event=None):
        c = len(self.message_numbers_entries) + 2

        number_entry = tk.Entry(self.msg_frame)
        self.message_numbers_entries.append(number_entry)
        number_entry.grid(column=0, row=c, **self.small_pads)

        text_entry = tk.Entry(self.msg_frame)
        self.message_texts_entries.append(text_entry)
        text_entry.grid(column=1, row=c)

        content_path_entry = tk.Entry(self.msg_frame)
        self.message_content_paths_entries.append(content_path_entry)
        content_path_entry.grid(column=2, row=c)

        delay_entry = tk.Entry(self.msg_frame)
        self.message_delays_entries.append(delay_entry)
        delay_entry.grid(column=3, row=c)

        current_option = self.type_options[0]
        type_option_var = tk.StringVar(self.msg_frame)
        self.type_option_vars.append(type_option_var)
        type_option_menu = ttk.OptionMenu(self.msg_frame, type_option_var, current_option,
                                          *self.type_options)
        self.message_type_menues.append(type_option_menu)
        type_option_menu.grid(column=4, row=c)

    def print_error(self, text):
        self.error_label["fg"] = "red"
        self.error_label["text"] = text

    def print_success(self, text):
        self.error_label["fg"] = "green"
        self.error_label["text"] = text

    def save_answer(self, event=None):
        answer_name = self.answer_name_entry.get()
        answer_keywords = self.keywords_entry.get()
        if not answer_name:
            self.print_error("Заполните название")
            return
        if answer_name in self.answers_names and not self.current_answer_id:
            self.print_error("На этом аккаунте уже существует цепочка с таким именем")
            return

        if not self.current_answer_id:
            self.current_answer_id = base_handler.add_answer(self.user_id, answer_name, answer_keywords,
                                                             self.pause_entry.get(), self.grop_value.get(),
                                                             not self.self_react_value.get(),
                                                             self.in_ignore_value.get())
        else:
            base_handler.update_answer(self.current_answer_id, name=answer_name, keywords=answer_keywords,
                                       pause=self.pause_entry.get(), group=self.grop_value.get(), self_ignore = not self.self_react_value.get(),
                                       in_ignore = self.in_ignore_value.get())

        messages = []
        for i in range(len(self.message_numbers_entries)):
            number = self.message_numbers_entries[i].get()
            text = self.message_texts_entries[i].get()
            path = self.message_content_paths_entries[i].get()
            delay = self.message_delays_entries[i].get()
            type_str = self.type_option_vars[i].get()

            if number:
                try:
                    number = int(number)
                except ValueError:
                    self.print_error(f"{number} не число")
                    return
                try:
                    delay = int(delay)
                except ValueError:
                    self.print_error(f"Задержка введена не корректно")
                    return

                type_ = self.type_options.index(type_str)

                messages.append([self.current_answer_id, number, type_, text, path, delay])

        base_handler.remove_messages_by_answer_id(self.current_answer_id)
        for row in messages:
            base_handler.add_message(*row)
        self.print_success("Цепочка сохранена")
        self.update_option_menu()


def run():
    root = tk.Tk()
    root.title("Настройки автоответчика")
    root_app = ApplicationAccountSettings(root, 1)
    root_app.mainloop()


if __name__ == '__main__':
    run()
