from flask import request, jsonify
from app import app
from app import db

from app.models import Order

@app.route('/order', methods=['POST'])
def create_order():
    data = request.json
    book_id = data['book_id']
    user_id = data['user_id']
    quantity = data.get('quantity')
    price = data['price']
    new_order = Order(book_id=book_id, quantity=quantity, price=price,user_id=user_id)
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({"order_id": new_order.id, "status": new_order.status}), 201