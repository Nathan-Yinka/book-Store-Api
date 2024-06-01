from marshmallow import fields, validates, ValidationError,Schema,pre_load,validate


class OrderSchema(Schema):
    id = fields.UUID()
    user_id = fields.Int()
    total_price = fields.Float()
    status = fields.Str()
    created_at = fields.DateTime()