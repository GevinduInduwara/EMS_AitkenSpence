from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2 import extras
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import bcrypt
import jwt
from functools import wraps

load_dotenv()
user_bp = Blueprint('users', __name__)
login_logs_bp = Blueprint('login_logs', __name__)

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:Gevindu@localhost:5433/Security-Attendance")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")

# Token authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Authentication token is missing'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = data['emp_no']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated

@user_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        required_fields = ['emp_no', 'name', 'rank', 'tel', 'company_name', 'security_firm', 'role', 'password']
        
        # Ensure all required fields are provided
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400

        # Check if the emp_no already exists
        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        db.execute("SELECT 1 FROM users WHERE emp_no = %s", (data['emp_no'],))
        if db.fetchone():
            db.close()
            client.close()
            return jsonify({'message': 'Employee number already exists'}), 400

        # Check if the company exists
        db.execute("SELECT 1 FROM company WHERE company_name = %s", (data['company_name'],))
        if not db.fetchone():
            db.close()
            client.close()
            return jsonify({
                'message': f"Company '{data['company_name']}' does not exist. Please add the company first."
            }), 400

        # Check if user already exists by telephone
        db.execute("SELECT 1 FROM users WHERE tel = %s", (data['tel'],))
        if db.fetchone():
            db.close()
            client.close()
            return jsonify({'message': 'User with this telephone number already exists'}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt(rounds=12))

        # Insert new user into the database
        db.execute("""
            INSERT INTO users (
                emp_no, name, rank, tel, company_name, security_firm, role, password
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING emp_no
        """, (
            data['emp_no'], data['name'], data['rank'], data['tel'], 
            data['company_name'], data['security_firm'], 
            data['role'], hashed_password.decode('utf-8')
        ))
        
        emp_no = db.fetchone()[0]
        client.commit()

        # Generate JWT token
        token = jwt.encode({
            'emp_no': emp_no, 
            'exp': datetime.utcnow() + timedelta(days=1)
        }, SECRET_KEY, algorithm="HS256")

        db.close()
        client.close()

        return jsonify({
            'message': 'User registered successfully',
            'emp_no': emp_no,
            'token': token
        }), 201

    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'message': f'Error during signup: {str(e)}'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        # Get login data from request
        data = request.get_json()
        
        # Validate required fields
        if not data or 'emp_no' not in data or 'password' not in data:
            return jsonify({'message': 'Employee number and password are required'}), 400

        # Connect to database
        try:
            client = psycopg2.connect(database_url)
            db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except Exception as conn_error:
            print(f"Database connection error: {conn_error}")
            return jsonify({'message': 'Database connection failed'}), 500

        # Find user by employee number (correct table used: 'users')
        db.execute("SELECT * FROM users WHERE emp_no = %s", (data['emp_no'],))
        user = db.fetchone()

        # Check if user exists
        if not user:
            db.close()
            client.close()
            return jsonify({'message': 'Invalid employee number'}), 401

        # STRICT CHECK: Only allow OIC login
        if str(user['role']).strip() != 'OIC':
            db.close()
            client.close()
            return jsonify({
                'message': 'Access Denied',
                'error': 'Only OIC users are allowed to log in',
                'actual_role': user['role']
            }), 403

        # Verify password
        try:
            # Convert stored and input passwords to bytes
            stored_password = user['password'].encode('utf-8')
            input_password = data['password'].encode('utf-8')
            
            # Check password
            if not bcrypt.checkpw(input_password, stored_password):
                db.close()
                client.close()
                return jsonify({'message': 'Invalid password'}), 401
        except Exception as e:
            print(f"Password verification error: {e}")
            db.close()
            client.close()
            return jsonify({'message': 'Authentication error'}), 500

        # Get client IP and device info
        ip_address = request.remote_addr if request.remote_addr else 'Unknown'
        device_info = request.user_agent.string if request.user_agent else 'Unknown'

        # Prepare log data with safe defaults
        log_data = {
            'emp_no': user['emp_no'], 
            'name': user['name'], 
            'department': user['department'],
            'role': user['role'], 
            'tel': user['tel'],
            'company_name': user.get('company_name', ''),
            'security_firm': user.get('security_firm', ''),
            'rank': user.get('rank', ''),
            'ip_address': ip_address, 
            'device_info': device_info,
            'status': 'SUCCESS'
        }

        # Insert or update login log for OIC
        try:
            # Detailed logging of user data
            print("Attempting to insert/update login log with data:")
            for key, value in log_data.items():
                print(f"{key}: {value}")

            # Insert or update login log using emp_no as primary key
            db.execute("""
                INSERT INTO login_logs (
                    emp_no, name, department, role, tel, 
                    company_name, security_firm, rank, 
                    ip_address, device_info, status
                ) VALUES (
                    %(emp_no)s, %(name)s, %(department)s, %(role)s, %(tel)s, 
                    %(company_name)s, %(security_firm)s, %(rank)s, 
                    %(ip_address)s, %(device_info)s, %(status)s
                )
                ON CONFLICT (emp_no) DO UPDATE SET
                    login_time = CURRENT_TIMESTAMP,
                    ip_address = %(ip_address)s,
                    device_info = %(device_info)s,
                    status = %(status)s
            """, log_data)
            
            # Commit the transaction
            client.commit()
            print("Login log inserted/updated successfully!")
        except Exception as log_error:
            # Rollback the transaction
            client.rollback()
            print(f"Error inserting login log: {log_error}")
            import traceback
            traceback.print_exc()

        # Generate JWT token
        token = jwt.encode({
            'emp_no': user['emp_no'], 
            'exp': datetime.utcnow() + timedelta(days=1)
        }, SECRET_KEY, algorithm="HS256")
        
        # Close database connection
        db.close()
        client.close()

        # Prepare response
        return jsonify({
            'message': 'Login successful', 
            'emp_no': user['emp_no'],
            'name': user['name'],
            'role': user['role'],
            'token': token
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error during login: {str(e)}'}), 500

@login_logs_bp.route('/logs', methods=['GET'])
def get_login_logs():
    try:
        # Get authentication token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization token is missing'}), 401

        # Remove 'Bearer ' if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        # Verify the token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_emp_no = payload.get('emp_no')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        # Connect to database
        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Verify current user is OIC
        db.execute("SELECT role FROM users WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()
        
        # Check if user is OIC
        if not current_user or current_user['role'] != 'OIC':
            db.close()
            client.close()
            return jsonify({'message': 'Only OIC can view login logs'}), 403

        # Fetch login logs (last 50 entries)
        db.execute("""
            SELECT 
                emp_no, name, department, role, tel, 
                company_name, security_firm, rank,
                TO_CHAR(login_time, 'YYYY-MM-DD HH24:MI:SS') as formatted_login_time, 
                ip_address, device_info, status, 
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as formatted_created_at
            FROM login_logs 
            ORDER BY login_time DESC 
            LIMIT 50
        """)
        
        login_logs = db.fetchall()
        
        # Close database connection
        db.close()
        client.close()

        # Convert to list of dictionaries for JSON serialization
        logs_list = []
        for log in login_logs:
            logs_list.append({
                'emp_no': log['emp_no'],
                'name': log['name'],
                'department': log['department'],
                'role': log['role'],
                'tel': log['tel'],
                'company_name': log['company_name'],
                'security_firm': log['security_firm'],
                'rank': log['rank'],
                'login_time': log['formatted_login_time'],
                'ip_address': log['ip_address'],
                'device_info': log['device_info'],
                'status': log['status'],
                'created_at': log['formatted_created_at']
            })

        return jsonify({
            'message': 'Login logs retrieved successfully',
            'total_logs': len(logs_list),
            'logs': logs_list
        }), 200

    except Exception as e:
        print(f"Error retrieving login logs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error retrieving logs: {str(e)}'}), 500
