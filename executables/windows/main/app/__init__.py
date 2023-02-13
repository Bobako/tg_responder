import asyncio
import logging
from threading import Thread

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flaskwebgui import FlaskUI

from app.config import config

flask_app = Flask(__name__)
flask_app.secret_key = config["FLASK"]["secret_key"]
flask_app.config['SQLALCHEMY_DATABASE_URI'] = config["DATABASE"]["uri"]
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(flask_app)
loop = asyncio.get_event_loop()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from app import models

db.create_all()

from app.bot import init_workers

bot_thread = Thread(target=init_workers, args=(loop,), daemon=True)
bot_thread.start()  # run all accounts in other thread

from app import routes

gui_app = FlaskUI(flask_app, maximized=True)
