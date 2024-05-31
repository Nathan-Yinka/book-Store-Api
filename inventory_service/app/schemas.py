from marshmallow import fields, validates, ValidationError,Schema,pre_load,validate,validates_schema
from .models import Inventory
from app import db,app


class OrderInventorySchema(Schema):
    book_id = fields.Int(required=True)
    quantity = fields.Int(required=True,validate=validate.Range(min=1))
    id = fields.UUID()
    
    @validates_schema
    def validate(self,data,**kwargs):
        
        book_id = data.get('book_id')
        inventory_item = Inventory.query.filter_by(book_id=book_id).first()
        if not inventory_item:
            raise ValidationError('Book does not exist')
        
        
class InventorySchema(Schema):
    book_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
            


        