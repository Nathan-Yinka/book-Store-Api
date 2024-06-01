import json
from threading import Thread
import requests
from flask import request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,create_refresh_token,decode_token
from flask_socketio import join_room, leave_room, emit, disconnect

from app import app
from app import db
from app.schemas import BookSchema,UserSchema
from app.models import Book,User,CartItem
from .connection import publish_message
from .connection import consume_messages
from app import socketio
from app import client

# Initialize schemas
book_schema = BookSchema()
user_schema = UserSchema()

# Callback function for message consumption
def callback(message,properties):
    
        try:
            data = json.loads(message)
            if properties.content_type == "order_created":
                print("order created")
                
            elif properties.content_type == "order_updated":
                # Emit order status update to connected users
                socketio.emit('order_status', {'order_id': data["order_id"], 'status': data["status"]}, room=data['user_id'] )
                print("order notification sent to socket")
                print("order updated")
                        
            elif properties.content_type == "stock_updated":
                # Update book stock
                book = Book.query.filter_by(id=data["book_id"]).first()
                if book:
                    book.available_quantity = data["quantity"]
                    db.session.add(book)
                    db.session.commit()
                    print("book stock updated")
                
        except Exception as err:
            print(err)
            raise Exception(err)
    
# Function to start message consumption thread
def start_consuming(queue,callback):
    thread = Thread(target=consume_messages, args=(queue, callback))
    thread.daemon = True
    thread.start()

# Start consuming messages
start_consuming("book",callback)


# Route to get all books
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    serialized_books = book_schema.dump(books, many=True)
    return jsonify(serialized_books), 200


# Route to get a single book by ID
@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    serialized_book = book_schema.dump(book)
    return jsonify(serialized_book), 200


# Route to add a new book
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
    

# Route to place an order
@app.route("/order", methods=["POST"])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400
    
    total_price = 0
    errors = []
    order_items = []
    for item in cart_items:
        total_price += item.book.price * item.quantity
        if item.book.available_quantity < item.quantity:
            errors.append(f"Insufficient stock for {item.book.title}")
        else:
            order_items.append({
                "book_id": item.book_id,
                "quantity": item.quantity,
                "price": item.book.price
            })

    if errors:
        return jsonify({"errors": errors}), 400
    
    order_data = {
        "user_id": user_id,
        "total_price": total_price,
        "items": order_items
    }
    
    ORDER_SERVICE_URL ="http://order-service:5003/order"
    try:
        response = requests.post(ORDER_SERVICE_URL, json=order_data)
        response.raise_for_status()
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
   
# Route to view orders 
@app.route("/view-orders", methods=["GET"])
@app.route("/view-orders/<uuid:order_id>", methods=["GET"])
@jwt_required()
def view_orders(order_id=None):
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "user_id must be provided"}), 400
    
    ORDER_SERVICE_URL ="http://order-service:5003"

    try:
        if order_id:
            response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}", params={"user_id": user_id})
        else:
            response = requests.get(f"{ORDER_SERVICE_URL}/order", params={"user_id": user_id})

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json().get("error", "Failed to fetch orders")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    

# Route to add a book to the cart
@app.route('/cart/', methods=['POST'])
@jwt_required()
def add_to_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    book_id = data.get('book_id')
    quantity = data.get('quantity')
    
    if not all([user_id, book_id, quantity]):
        return jsonify({"error": "Missing data"}), 400
    book = Book.query.get(book_id)
    

    if book.available_quantity < quantity:
        return jsonify({"error": "Insufficient stock"}), 400
    
    cart_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()

    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id,quantity=quantity,book_id=book_id)
        db.session.add(cart_item)
        
    try:
        db.session.commit()
        return jsonify({"message": "Item added to cart"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
 
 
# Route to delete a book from the cart   
@app.route('/cart/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_from_cart(book_id):
    user_id = get_jwt_identity()
    
    if not user_id or not book_id:
        return jsonify({"error": "Missing user_id or book_id"}), 400

    cart_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()
    
    if not cart_item:
        return jsonify({"error": "Item not found in cart"}), 404

    try:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": "Item removed from cart"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Route to update the cart
@app.route('/cart/', methods=['PUT'])
@jwt_required()
def update_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    book_id = data.get('book_id')
    quantity = data.get('quantity')
    
    if not all([user_id, book_id, quantity]):
        return jsonify({"error": "Missing data"}), 400

    if quantity <= 0:
        return jsonify({"error": "Quantity must be greater than 0"}), 400

    cart_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not cart_item:
        return jsonify({"error": "Item not found in cart"}), 404

    cart_item.quantity = quantity

    try:
        db.session.commit()
        return jsonify({"message": "Cart updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    

@app.route('/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"message": "Cart cleared successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    if not cart_items:
        return jsonify({"cart": []}), 200
    
    cart_data = []
    for item in cart_items:
        cart_data.append({
            "book_id": item.book_id,
            "title": item.book.title,
            "quantity": item.quantity,
            "price": item.book.price,
            "total_price": item.quantity * item.book.price
        })
    
    return jsonify(cart_data), 200



#----------------------------------------- SocketIO connection event-----------------------------------------------
@socketio.on('connect')
def handle_connect():
    token = extract_token_from_header(request.headers.get('Authorization'))
    if not token:
        disconnect()  # Disconnect if the token extraction fails
        return

    user_id = get_user_id_from_token(token)
    if user_id:
        join_room(user_id)
        print(f'User {user_id} connected and joined room {user_id}')
    else:
        print('Authentication failed')
        disconnect()


# SocketIO disconnection event
@socketio.on('disconnect')
def handle_disconnect():
    token = extract_token_from_header(request.headers.get('Authorization'))
    if not token:
        return

    user_id = get_user_id_from_token(token)
    if user_id:
        leave_room(user_id)
        print(f'User {user_id} disconnected and left room {user_id}')



# Function to extract user ID from JWT token
def get_user_id_from_token(token):
    try:
        decoded_token = decode_token(token)
        return decoded_token['sub']
    except Exception as e:
        return None

# Function to extract token from authorization header
def extract_token_from_header(authorization_header):
    if not authorization_header:
        print('No Authorization header provided')
        return None
    header_parts = authorization_header.split()
    if len(header_parts) != 2 or header_parts[0].lower() != 'bearer':
        print('Invalid Authorization header format')
        return None

    return header_parts[1]


# Route to summarize a book
@app.route('/summarize-book/<int:book_id>', methods=['GET'])
def summarize_book(book_id):

    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    book_text = book.content
    
    if not book_text:
        return jsonify({'error': "No content"})

    try:
        
        response = client.completions.create(
            model="gpt-3.5-turbo-0613",
            prompt=book_text,
            max_tokens=100,
            temperature=0.5,
            top_p=1,
            n=1,
            stop=["\n"]
        )

        summary = response['choices'][0]['text']
        return jsonify({'summary': summary})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#------------------------------------  Authentication Routes   ------------------------------------------------------------------ #
# Route for user registration
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


# Route for user login
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
    
    
# Route to refresh access token
@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify(access_token=access_token)