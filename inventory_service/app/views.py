from threading import Thread
import json
from marshmallow import ValidationError
from flask import request, jsonify

from app import app
from app import db
from .schemas import OrderInventorySchema,InventorySchema
from .models import Inventory
from .connection import consume_messages
from .connection import publish_message

order_inventory_schema = OrderInventorySchema()
inventory_schema = InventorySchema()

def callback(message,properties):
    with app.app_context():
        try:
            data = json.loads(message)
            if properties.content_type == "order_created":
                try:
                    order_data = order_inventory_schema.load(data)
                except ValidationError as err:
                    print(err)
                    publish_message(json.dumps(data),"order_error","order")
                    return
                print(order_data["book_id"])
                inventory_item = Inventory.query.filter_by(book_id=order_data["book_id"]).first()
                quantity = order_data['quantity']
                
                if inventory_item.quantity < quantity:
                    publish_message(json.dumps(data),"order_error","order")
                    update_inventory(inventory_item,inventory_item.quantity)
                else:
                    remaining_quantity = inventory_item.quantity - quantity
                    update_inventory(inventory_item,remaining_quantity)
                    
                    
            elif properties.content_type == "book_created":
                item = Inventory(book_id=data["id"],quantity=data["available_quantity"])
                db.session.add(item)
                db.session.commit()
                print("added to inventory")
            
        
        except Exception as err:
            print(err)
            raise Exception(err)
    
def start_consuming(queue,callback):
    thread = Thread(target=consume_messages, args=(queue, callback))
    thread.daemon = True
    thread.start()

start_consuming("inventory",callback)

def update_inventory(inventory_item,quantity):
    inventory_item.quantity = quantity
    
    db.session.add(inventory_item)
    db.session.commit()
    print(inventory_item.quantity)
    print(inventory_item.quantity)
    print(inventory_item.quantity)
    print(inventory_item.quantity)
    data = inventory_schema.dump(inventory_item)
    print("send book stock")
    publish_message(json.dumps(data),"stock_updated","book")
    