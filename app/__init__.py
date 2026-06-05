from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
app = Flask(__name__)

def create_app():
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from . import routes, models
        db.create_all()

    return app