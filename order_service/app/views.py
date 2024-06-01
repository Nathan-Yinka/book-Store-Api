from threading import Thread
import json
from marshmallow import ValidationError
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app import app
from app import db
from .schemas import OrderSchema
from .connection import consume_messages
from .connection import publish_message
from app.models import Order,OrderItem

order_schema = OrderSchema()

def callback(message,properties):
    with app.app_context():
        try:
            data = json.loads(message)
            if properties.content_type == "order_error":
                try:
                    order_id = data["order_id"]
                    order = Order.query.filter_by(id=order_id).first()
                    order.status = "Out Of Stock"
                    db.session.add(order)
                    db.session.commit()
                    update_order(order,"Out of stock (processing refund)")
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
    if not data.get('user_id') or not data.get('items'):
        return jsonify({"error": "Invalid order data"}), 400

    user_id = data.get('user_id')
    items = data.get('items')
    total_price = data.get('total_price')
    
    order = Order(user_id=user_id, total_price=total_price)
    db.session.add(order)
    db.session.flush()  # Get the order ID before committing
    
    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            book_id=item['book_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
        
    try:
        db.session.commit()
        inventory_updates = [{"book_id": item['book_id'], "quantity": item['quantity']} for item in items]
        publish_message(json.dumps({"inventory_updates":inventory_updates,"order_id":order.id}),"order_created","inventory")
        
        return jsonify({"message": "Order created successfully", "order_id": order.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/order/<uuid:order_id>/status', methods=['PATCH'])
def change_order_status(order_id):
    new_status = request.json.get('status')
    if not new_status:
        return jsonify({"error": "Status field is required"}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    update_order(order,new_status)
  
    return jsonify({"message": "Order status updated successfully", "order_id": order_id, "status": new_status}), 200

@app.route('/orders', methods=['GET'])
def list_orders():
    try:
        orders = Order.query.all()
        result = order_schema.dump(orders, many=True)
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_order(order,status):
    order.status = status
    db.session.add(order)
    db.session.commit()
    payload = {"order_id":str(order.id),"status":order.status,"user_id":order.user_id}
    publish_message(json.dumps(payload),"order_updated","book")
    
    
@app.route("/order", methods=["GET"])   
@app.route("/order/<uuid:order_id>", methods=["GET"])   
def get_order(order_id=None):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error":"user_id must be provided"})
    try:
        if order_id:
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()
            if not order:
                return jsonify({"error": "Order not found"}), 404
            result = order_schema.dump(order)
        else:
            orders = Order.query.filter_by(user_id=user_id).all()
            result = order_schema.dump(orders, many=True)
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
