import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://root:admin@book-service-db:5432/book_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-proj-OpxxGWjx4aFNvIC96V9OT3BlbkFJszSBNFPAsp3w7idvyjsw')
    SECRET_KEY = "mjrjndjm33049ejsifnri4ifji4ie3iorjd"
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=5)
    
