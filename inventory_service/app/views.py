from threading import Thread
import json
from marshmallow import ValidationError
from flask import request, jsonify

from app import app
from app import db
from .schemas import OrderInventorySchema, InventorySchema
from .models import Inventory
from .connection import consume_messages
from .connection import publish_message

# Initialize schemas
order_inventory_schema = OrderInventorySchema()
inventory_schema = InventorySchema()

# Callback function to handle incoming messages from the queue
def callback(message, properties):
    with app.app_context():
        try:
            data = json.loads(message)
            
            if properties.content_type == "order_created":
                order_id = data.get("order_id")
                error = None
                
                # Process each item in the order
                for item in data['inventory_updates']:
                    book_id = item.get('book_id')
                    quantity = item.get('quantity')
                    
                    # Retrieve the inventory item
                    inventory_item = Inventory.query.get(book_id)
                    
                    if inventory_item:
                        if inventory_item.quantity >= quantity:
                            # Update the inventory if there's enough stock
                            remaining_quantity = inventory_item.quantity - quantity
                            update_inventory(inventory_item, remaining_quantity)
                        else:
                            # Handle the case where there's not enough stock
                            error = True
                            update_inventory(inventory_item, 0)
                
                if error:
                    # Publish a message indicating an error with the order
                    publish_message(json.dumps({"order_id": order_id}), "order_error", "order")
                    
            elif properties.content_type == "book_created":
                # Add new book to the inventory
                item = Inventory(book_id=data["id"], quantity=data["available_quantity"])
                db.session.add(item)
                db.session.commit()
                print("Added to inventory")
                
        except Exception as err:
            print(err)
            raise Exception(err)

# Function to start consuming messages from the specified queue
def start_consuming(queue, callback):
    thread = Thread(target=consume_messages, args=(queue, callback))
    thread.daemon = True
    thread.start()

start_consuming("inventory", callback)

# Function to update inventory and publish a stock update message
def update_inventory(inventory_item, quantity):
    inventory_item.quantity = quantity
    
    db.session.add(inventory_item)
    db.session.commit()
    
    data = inventory_schema.dump(inventory_item)
    print(f"Sending book stock update for {inventory_item.book_id}")
    
    # Publish a message indicating that the stock has been updated
    publish_message(json.dumps(data), "stock_updated", "book")
