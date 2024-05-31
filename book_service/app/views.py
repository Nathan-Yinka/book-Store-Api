import json
from threading import Thread
import requests
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,create_refresh_token

from app import app
from app import db
from app.schemas import BookSchema,UserSchema,OrderSchema,GetOrderSchema
from app.models import Book,User,Order
from .connection import publish_message
from .connection import consume_messages


book_schema = BookSchema()
user_schema = UserSchema()
order_schema = OrderSchema()
get_order_schema = GetOrderSchema()

def callback(message,properties):
    with app.app_context():
        try:
            data = json.loads(message)
            if properties.content_type == "order_created":
                order = Order(**data)
                db.session.add(order)
                db.session.commit()
                print("order created")
                
            elif properties.content_type == "order_updated":
                order = Order.query.filter_by(id=data["id"]).first()
                if order:
                    order.status = data["status"]
                    db.session.add(order)
                    db.session.commit()
                    print("order updated")
                        
            elif properties.content_type == "stock_updated":
                book = Book.query.filter_by(id=data["book_id"]).first()
                if book:
                    book.available_quantity = data["quantity"]
                    db.session.add(book)
                    db.session.commit()
                    print("book stock updated")
                
        except Exception as err:
            print(err)
            raise Exception(err)
    
def start_consuming(queue,callback):
    thread = Thread(target=consume_messages, args=(queue, callback))
    thread.daemon = True
    thread.start()

start_consuming("book",callback)


@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    serialized_books = book_schema.dump(books, many=True)
    return jsonify(serialized_books), 200


@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    serialized_book = book_schema.dump(book)
    return jsonify(serialized_book), 200

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    try:
        book_data = book_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    book = Book(**book_data)
    db.session.add(book)
    db.session.commit()
    book_data = book_schema.dump(book)
    publish_message(json.dumps(book_data),"book_created","inventory")

    return jsonify(book_data), 201
    
    
@app.route("/order", methods=["POST"])
@jwt_required()
def place_order():
    data = request.get_json()
    
    try:
        order_data = order_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    book_id = order_data['book_id']
    book = Book.query.get(book_id)
    price = book.price
    quantity = order_data['quantity']
    
    user_id = get_jwt_identity()
    
    order_data = {
        "book_id": book_id,
        "quantity": quantity,
        "price":price,
        "user_id" : user_id
    }
    ORDER_SERVICE_URL ="http://order-service:5003/order"
    try:
        response = requests.post(ORDER_SERVICE_URL, json=order_data)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/order", methods=["GET"])   
@app.route("/order/<uuid:order_id>", methods=["GET"])   
@jwt_required()
def get_order(order_id=None):
    user_id = get_jwt_identity()
    try:
        if order_id:
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()
            if not order:
                return jsonify({"error": "Order not found"}), 404
            result = get_order_schema.dump(order)
        else:
            orders = Order.query.filter_by(user_id=user_id).all()
            result = get_order_schema.dump(orders, many=True)
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#  Authentication Routes
@app.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    try:
        user_data = user_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    new_user = User(**user_data)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify(user_schema.dump(new_user)), 201


@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    
    if not password:
        return jsonify({"error":"password field can not be empty"})
    if not username.strip():
        return jsonify({"error":"username field can not be empty"})
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify(access_token=access_token,refresh_token=refresh_token), 200
    
    else:
        return jsonify({'message': 'Invalid credentials'}), 401   
    
@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify(access_token=access_token)