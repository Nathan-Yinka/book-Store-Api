from app import db,bcrypt

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    available_quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"<Book {self.title} by {self.author}>"
    


class User(db.Model):
    
    def __init__(self,username,password):
        self.username = username
        self.set_password(password)
        
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(length=30), nullable=False,unique=True)
    password_hash = db.Column(db.String(length=60),nullable=False)
    
    def __repr__(self):
        return self.username
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return self.username
        