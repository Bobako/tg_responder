import asyncio
from threading import Thread

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flaskwebgui import FlaskUI

from app.config import config
from app.bot import init_workers

flask_app = Flask(__name__)
flask_app.secret_key = config["FLASK"]["secret_key"]
flask_app.config['SQLALCHEMY_DATABASE_URI'] = config["DATABASE"]["uri"]
# flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(flask_app)
loop = asyncio.get_event_loop()

from app import models

db.create_all()
Thread(target=init_workers, args=(db.session, loop)).start()  # run all accounts in other thread

from app import routes

gui_app = FlaskUI(flask_app, maximized=True)
