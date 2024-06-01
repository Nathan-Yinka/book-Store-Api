import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://root:admin@inventory-service-db:5431/inventory_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "mjrjndjm33049ejsifnri4ifji4ie3iorjd"
    
