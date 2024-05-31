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

def callback(message):
    print(message)
    
def start_consuming():
    thread = Thread(target=consume_messages, args=("book", callback))
    thread.daemon = True
    thread.start()

start_consuming()


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
    publish_message(json.dumps(payload),"order")
    return jsonify(payload), 201

