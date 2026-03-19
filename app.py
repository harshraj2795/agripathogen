import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db, login_manager, mail, bcrypt

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///agripathogen.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH']             = 16 * 1024 * 1024

    app.config['MAIL_SERVER']         = os.getenv('MAIL_SERVER',  'smtp.gmail.com')
    app.config['MAIL_PORT']           = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS']        = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 30
    app.config['SESSION_COOKIE_HTTPONLY']  = True
    app.config['SESSION_COOKIE_SAMESITE']  = 'Lax'

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)

    from blueprints.auth import auth
    from blueprints.main import main
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)