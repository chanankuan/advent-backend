from dotenv import load_dotenv

import os

from datetime import timedelta
from flask import Flask, session
from flask_cors import CORS


def create_app(test_config=None):
    # Load environment variables from the .env file
    load_dotenv()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
	# Support requests from the frontend localhost
    CORS(app, supports_credentials=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'), 
        DATABASE=os.path.join(app.instance_path, 'advent.db'),
    )
    
    # Required for cross-origin cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
	# Set to True in production with HTTPS
    app.config['SESSION_COOKIE_SECURE'] = True 
	# Set the session to be permanent and define its lifetime (e.g., 30 minutes)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    # @app.route('/hello')
    # def hello():
    #     return 'Hello, World!'
    
    from . import db
    db.init_app(app)

    from . import auth, calendar
    app.register_blueprint(auth.bp)
    app.register_blueprint(calendar.bp)

    return app

app = create_app()