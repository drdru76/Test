import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('sqlite:///'):
        # Ensure relative sqlite paths are absolute to avoid ambiguity with instance folder
        db_path = SQLALCHEMY_DATABASE_URI[10:]
        if not os.path.isabs(db_path):
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, db_path)
    
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    AI_API_KEY = os.environ.get('AI_API_KEY')
    AI_PROVIDER = os.environ.get('AI_PROVIDER') or 'openai' # default to openai
    AI_BASE_URL = os.environ.get('AI_BASE_URL')
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
    WEBHOOK_REPO_PATH = os.environ.get('WEBHOOK_REPO_PATH') or basedir
