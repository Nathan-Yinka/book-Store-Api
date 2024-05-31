from marshmallow import fields, validates, ValidationError,Schema,pre_load,validate

from .models import Book,User

# To serialize the data
class BookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    author = fields.Str(required=True)
    price = fields.Float(required=True)
    available_quantity = fields.Int(required=True)
    description = fields.Str(required=True)
    
    @validates('price')
    def validate_price(self, value):
        if value <= 0:
            raise ValidationError('Price must be greater than zero.')
        
    @validates('available_quantity')
    def validate_available_quantity(self, value):
        if value < 0:
            raise ValidationError('Available quantity must be greater than or equal to zero.')
        
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True,load_only=True)
    
    @validates('username')
    def validate_username(self, username):
        if not username.strip():
            raise ValidationError('username cannot be empty')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            raise ValidationError('User with this username already exists.')
        
    @validates("password")
    def validate_password(self,password):
        if not password:
            raise ValidationError("Password cannot be empty")
        
    @pre_load
    def preprocess_data(self, data, **kwargs):
        if 'username' in data:
            data['username'] = data['username'].strip()
        return data
    
    
class OrderSchema(Schema):
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    book_id = fields.Int(required=True)

    @validates("book_id")
    def validate_id(self, value):
        book = Book.query.get(value)
        if not book:
            raise ValidationError("Book with id '{}' not found".format(value))
        self.context["book"] = book

    @validates("quantity")
    def validate_quantity(self, value):
        book = self.context.get("book")
        if not book:
            raise ValidationError("Book ID must be validated before quantity")
        if book.available_quantity < value:
            raise ValidationError("Book quantity is more than current stock")
        


class GetOrderSchema(Schema):
    id = fields.UUID()
    book_id = fields.Int()
    user_id = fields.Int()
    quantity = fields.Int()
    price = fields.Float()
    total = fields.Float()
    status = fields.Str()