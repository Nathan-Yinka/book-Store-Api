import os
from app import app,socketio

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    socketio.run(app,host='0.0.0.0', port=port,debug=True,allow_unsafe_werkzeug=True)