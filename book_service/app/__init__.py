import eventlet
eventlet.monkey_patch()
from flask import Flask
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, join_room, leave_room, emit, disconnect



from app.config import Config
from openai import OpenAI


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*" ,message_queue='amqp://guest:guest@rabbitmq:5672/')

client = OpenAI(
  api_key=app.config['OPENAI_API_KEY'],
)

migrate = Migrate(app, db)


from app import views,models