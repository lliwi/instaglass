import os
from flask import Flask


def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        DATABASE_HOST=os.environ.get('FLASK_DATABASE_HOST'),
        DATABASE_PASSWORD=os.environ.get('FLASK_DATABASE_PASSWORD'),
        DATABASE_USER=os.environ.get('FLASK_DATABASE_USER'),
        DATABASE=os.environ.get('FLASK_DATABASE'),
        APIFY_KEY=os.environ.get('APIFY_KEY'),
        OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')
    )

    
    from . import db
    db.init_app(app)

    from . import instaglass
    app.register_blueprint(instaglass.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    return app
