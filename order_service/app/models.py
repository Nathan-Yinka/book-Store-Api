from app import db
import uuid

class Order(db.Model):
    id = db.Column(db.String, primary_key=True)
    book_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False)
    
    def __init__(self, book_id,user_id, quantity, price):
        self.id = str(uuid.uuid4())
        self.book_id = book_id
        self.user_id = user_id
        self.quantity = quantity
        self.price = price
        self.status = "Processing"
        self.total = quantity * price