from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flaskwebgui import FlaskUI

from app.config import config

flask_app = Flask(__name__)
flask_app.secret_key = config["FLASK"]["secret_key"]
flask_app.config['SQLALCHEMY_DATABASE_URI'] = config["DATABASE"]["uri"]
# flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(flask_app)

from app import models, routes

db.create_all()
gui_app = FlaskUI(flask_app, maximized=True)
