from threading import Thread
import json
from marshmallow import ValidationError
from flask import request, jsonify

from app import app
from app import db
from .schemas import OrderSchema
from .connection import consume_messages
from .connection import publish_message
from app.models import Order

order_schema = OrderSchema()

def callback(message,properties):
    with app.app_context():
        try:
            data = json.loads(message)
            if properties.content_type == "order_error":
                try:
                    order_data = data["id"]
                    order = Order.query.filter_by(id=order_data).first()
                    order.status = "Out Of Stock"
                    db.session.add(order)
                    db.session.commit()
                    update_order(order,"Out of stock")
                except:
                    pass
        
        except Exception as err:
                raise Exception(err)
        

def start_consuming(queue,callback):
    thread = Thread(target=consume_messages, args=(queue, callback))
    thread.daemon = True
    thread.start()

start_consuming("order",callback)



@app.route('/order', methods=['POST'])
def create_order():
    data = request.json
    try:
        order = order_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    new_order = Order(**order)
    db.session.add(new_order)
    db.session.commit()
    payload = order_schema.dump(new_order)
    publish_message(json.dumps(payload),"order_created","book")
    publish_message(json.dumps({"book_id":payload["book_id"],"quantity":payload["quantity"],"id":payload["id"]}),"order_created","inventory")
    return jsonify(payload), 201



def update_order(order,status):
    order.status = status
    db.session.add(order)
    db.session.commit()
    payload = order_schema.dump(order)
    publish_message(json.dumps(payload),"order_updated","book")
    