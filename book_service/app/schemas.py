from marshmallow import fields, validates, ValidationError,Schema,pre_load,validate

from .models import User

# To serialize the data
class BookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    author = fields.Str(required=True)
    price = fields.Float(required=True)
    available_quantity = fields.Int(required=True)
    description = fields.Str(required=True)
    content = fields.Str(required=True)
    
    @validates('price')
    def validate_price(self, value):
        if value <= 0:
            raise ValidationError('Price must be greater than zero.')
        
    @validates('available_quantity')
    def validate_available_quantity(self, value):
        if value < 1:
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
    