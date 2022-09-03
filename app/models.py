from app import db

MSG_TYPE_TEXT = 0
MSG_TYPE_PHOTO = 1
MSG_TYPE_AUDIO = 2
MSG_TYPE_VIDEO = 3
MSG_TYPE_DOC = 4
MSG_TYPE_VIDEO_FILE = 5
MSG_TYPE_AUDIO_FILE = 6


class Account(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String)
    user_repr = db.Column(db.String)
    turned_on = db.Column(db.Boolean)

    group_number = db.Column(db.Integer)  # номер группы
    number = db.Column(db.Integer)  # номер акка в группе

    chains = db.relationship("Chain", back_populates="account", cascade="all, delete")

    status = db.Column(db.Integer)  # 0 - не активен, 1 - активен, -1 - ошибка

    def __init__(self, **kwargs):
        self.update(**kwargs)
        self.status = 0

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return self.user_repr


class Chain(db.Model):
    __tablename__ = "chain"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    keywords = db.Column(db.String)
    turned_on = db.Column(db.Boolean)
    pause_seconds = db.Column(db.Integer)  # время на которое выкл цепочка после использования
    used_at = db.Column(db.DateTime)  # последнее использование
    for_group = db.Column(db.Boolean)  # используется ли в группах
    self_ignore = db.Column(db.Boolean)  # игнорировать ли свои сообщ

    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    # если None, цепочка не прикреплена к пользователю и является шаблоном
    account = db.relationship("Account", back_populates="chains")

    messages = db.relationship("Message", back_populates="chain", cascade="all, delete")

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer)
    type = db.Column(db.Integer)
    text = db.Column(db.String)
    content_path = db.Column(db.String)
    delay_seconds = db.Column(db.Integer)

    chain_id = db.Column(db.Integer, db.ForeignKey("chain.id"))
    chain = db.relationship("Chain", back_populates="messages")

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)
