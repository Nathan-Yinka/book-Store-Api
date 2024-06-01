import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://root:admin@order-service-db:5432/order_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "mjrjndjm33049ejsifnri4ifji4ie3iorjd"
    
