from flask import Flask
from .db import db
from .models.user import User

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    with app.app_context():
        db.create_all()

        from .routes.profile import profile_bp
        from .routes.sync import sync_bp

        app.register_blueprint(profile_bp, url_prefix="/profile")
        app.register_blueprint(sync_bp, url_prefix="/sync")

    return app
