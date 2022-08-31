import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import copy

MSG_TYPE_TEXT = 0
MSG_TYPE_PHOTO = 1
MSG_TYPE_AUDIO = 2
MSG_TYPE_VIDEO = 3
MSG_TYPE_DOC = 4
MSG_TYPE_VIDEO_FILE = 5
MSG_TYPE_AUDIO_FILE = 6

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    contact = Column(String)
    active = Column(Boolean)
    user_str = Column(String)

    def __init__(self, contact, active, user_str):
        self.contact = contact
        self.active = active
        self.user_str = user_str

    def __repr__(self):
        return f"Id: {self.id}, contact: {self.contact}"


class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer)
    keywords = Column(String)
    active = Column(Boolean)
    pause = Column(Integer)
    used = Column(String)
    group = Column(Boolean)
    self_ignore = Column(Boolean)
    in_ignore = Column(Boolean)

    def __init__(self, user_id, name, keywords, active=True, pause=0, group=0, self_ignore = False, in_ignore = False):
        self.name = name
        self.user_id = user_id
        self.keywords = keywords
        self.active = active
        self.pause = pause
        self.used = ''
        self.group = group
        self.self_ignore = self_ignore
        self.in_ignore = in_ignore

    def __repr__(self):
        return f"Name: {self.name}, keywords: {self.keywords}"


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    answer_id = Column(Integer)
    type_ = Column(Integer)
    text = Column(String)
    content_path = Column(String)
    delay = Column(Integer)

    def __init__(self, answer_id, number, type_, text=None, content_path=None, delay=0):
        self.answer_id = answer_id
        self.number = number
        self.type_ = type_
        self.text = text
        self.content_path = content_path
        self.delay = delay

    def __repr__(self):
        return f"number: {self.number}, text: {self.text}"

class ActiveAnswer(Base):
    __tablename__ = 'active_answers'
    id = Column(Integer, primary_key = True)
    from_user_id = Column(Integer)
    to_user_id = Column(Integer)
    responded = Column(Boolean)

    def __init__(self, from_user_id, to_user_id):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.responded = False


engine = sqlalchemy.create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def respond_active_answer(from_user_id, to_user_id):
    session = Session()
    answer = session.query(ActiveAnswer).filter(ActiveAnswer.from_user_id == from_user_id).filter(
        ActiveAnswer.to_user_id == to_user_id).first()
    answer.responded = True
    session.commit()

def is_active_answer_respond(from_user_id, to_user_id):
    session = Session()
    answer = session.query(ActiveAnswer).filter(ActiveAnswer.from_user_id == from_user_id).filter(
        ActiveAnswer.to_user_id == to_user_id).first()
    session.close()
    responded =  answer.responded
    return responded


def add_active_answer(from_user_id,to_user_id):
    active_answer = ActiveAnswer(from_user_id,to_user_id)
    session = Session()
    session.add(active_answer)
    session.commit()

def is_answer_active(from_user_id, to_user_id):
    session = Session()
    if session.query(ActiveAnswer).filter(ActiveAnswer.from_user_id == from_user_id).filter(ActiveAnswer.to_user_id == to_user_id).first():
        return True
    else:
        return False

def remove_active_answer(from_user_id, to_user_id):
    session = Session()
    answer = session.query(ActiveAnswer).filter(ActiveAnswer.from_user_id == from_user_id).filter(
        ActiveAnswer.to_user_id == to_user_id).first()
    session.delete(answer)
    session.commit()

def clear_active_answers():
    session = Session()
    answers = session.query(ActiveAnswer).all()
    for answer in answers:
        session.delete(answer)
    session.commit()

def add_user(contact, active, user_str):
    user = User(contact, active, user_str)
    session = Session()
    session.add(user)
    session.commit()


def update_user(user_id, **kwargs):
    session = Session()
    user = session.query(User).filter(User.id == user_id).one()
    keys = list(kwargs.keys())

    for key in keys:
        if key == 'active':
            user.active = kwargs[key]
    session.commit()


def get_user(user_id):
    session = Session()
    user = session.query(User).filter(User.id == user_id).one()
    session.close()
    return copy.copy(user)


def get_users():
    session = Session()
    users = session.query(User).all()
    return copy.deepcopy(users)


def get_user_by_contact(contact):
    session = Session()
    user = session.query(User).filter(User.contact == contact).first()
    session.close()
    if user:
        return copy.copy(user)


def get_answers_by_user_id(user_id):
    session = Session()
    answers = session.query(Answer).filter(Answer.user_id == user_id).all()
    answers_copy = copy.deepcopy(answers)
    session.close()
    return answers_copy


def get_messages_by_answer_id(answer_id):
    session = Session()
    messages = session.query(Message).filter(Message.answer_id == answer_id).all()
    session.close()
    return copy.deepcopy(messages)


def sort_messages(messages):
    sorted = []
    numbers = [message.number for message in messages]
    while messages:
        sorted.append(messages.pop(numbers.index(min(numbers))))
        numbers.pop(numbers.index(min(numbers)))

    for i in range(len(sorted)):
        sorted[i].number = i + 1

    return sorted


def remove_messages_by_answer_id(answer_id):
    session = Session()
    messages = session.query(Message).filter(Message.answer_id == answer_id).all()
    for message in messages:
        session.delete(message)
    session.commit()


def add_message(answer_id, number, type_, text, path, delay):
    session = Session()
    message = Message(answer_id, number, type_, text, path, delay)
    session.add(message)
    session.commit()


def add_answer(user_id, name, keywords, pause, group=0, self_ignore = False, in_ignore = False):
    answer = Answer(user_id, name, keywords, pause=pause, group=group, self_ignore = self_ignore, in_ignore=in_ignore)
    session = Session()
    session.add(answer)
    session.commit()
    answer = session.query(Answer).filter(Answer.user_id == user_id).all()[-1]
    session.close()
    return answer.id


def update_answer(answer_id, **kwargs):
    session = Session()
    answer = session.query(Answer).filter(Answer.id == answer_id).one()
    for key in list(kwargs.keys()):
        if key == 'name':
            answer.name = kwargs[key]
        elif key == 'keywords':
            answer.keywords = kwargs[key]
        elif key == 'active':
            answer.active = kwargs[key]
        elif key == 'pause':
            answer.pause = kwargs[key]
        elif key == 'used':
            answer.used = kwargs[key]
        elif key == 'group':
            answer.group = kwargs[key]
        elif key == 'self_ignore':
            answer.self_ignore = kwargs[key]
        elif key == 'in_ignore':
            answer.in_ignore = kwargs[key]
    session.commit()


def get_answer_by_name(name, user_id):
    session = Session()
    answer = session.query(Answer).filter(Answer.name == name).filter(Answer.user_id == user_id).first()
    session.close()
    return copy.deepcopy(answer)


def get_active_answers(user_id):
    session = Session()
    answers = copy.copy(session.query(Answer).filter(Answer.user_id == user_id).filter(Answer.active == 1).all())
    session.close()
    return answers


def get_active_users():
    session = Session()
    users = session.query(User).filter(User.active).all()
    session.close()
    return users


def remove_answer(answer_id):
    session = Session()
    answer = session.query(Answer).filter(Answer.id == answer_id).one()
    remove_messages_by_answer_id(answer_id)
    session.delete(answer)
    session.commit()


def remove_account(user_id):
    session = Session()
    user = session.query(User).filter(User.id == user_id).one()
    session.delete(user)
    session.commit()


def get_user_by_user_str(user_str):
    session = Session()
    user = session.query(User).filter(User.user_str == user_str).one()
    session.close()
    return copy.copy(user)


def share_answer(answer, user_id):
    messages = get_messages_by_answer_id(answer.id)

    answer = Answer(user_id, answer.name, answer.keywords, answer.active, answer.pause, answer.group, answer.self_ignore, answer.in_ignore)
    session = Session()
    session.add(answer)
    answer_id = session.query(Answer).all()[-1].id

    for message in messages:
        new_message = Message(answer_id, message.number, message.type_, message.text, message.content_path,
                              message.delay)
        session.add(new_message)
    session.commit()
