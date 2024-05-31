from marshmallow import fields, validates, ValidationError,Schema,pre_load,validate


class OrderSchema(Schema):
    id = fields.UUID()
    book_id = fields.Int()
    user_id = fields.Int()
    quantity = fields.Int()
    price = fields.Float()
    total = fields.Float()
    status = fields.Str()