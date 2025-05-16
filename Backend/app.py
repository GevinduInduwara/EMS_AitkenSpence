import os
import psycopg2
from psycopg2 import extras
from datetime import datetime, timedelta
import bcrypt
import jwt
from functools import wraps
from flask import Flask
from flask_cors import CORS
from routes.user_routes import user_bp
from routes.attendance_routes import attendance_bp
from routes.company_routes import company_bp
from dotenv import load_dotenv
from models import initialize_database

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://192.168.1.100:5001", "http://192.168.1.100:8081"]}}, supports_credentials=True)

# Initialize database when app starts
with app.app_context():
    try:
        initialize_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(attendance_bp, url_prefix='/api')
app.register_blueprint(company_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
