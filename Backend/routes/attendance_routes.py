from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2 import extras
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import jwt

load_dotenv()
attendance_bp = Blueprint('attendance', __name__)

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:Gevindu@localhost:5433/Security-Attendance")

# Assuming SECRET_KEY is defined elsewhere in the code
SECRET_KEY = os.getenv("SECRET_KEY")

@attendance_bp.route('/mark', methods=['POST'])
def mark_attendance():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization token is missing'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        current_user_emp_no = payload.get('emp_no')

        data = request.get_json()
        emp_no = data.get('emp_no')
        print(f"Received data: {data}")
        print(f"Employee number: {emp_no}")
        
        if not emp_no:
            return jsonify({'message': 'Employee number is required'}), 400

        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Add debug logging for the query
        print(f"Executing query with emp_no: {emp_no}")

        # Check if current user is Acting Admin
        db.execute("SELECT role FROM employees WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()

        if not current_user or current_user['role'] != 'Acting Admin':
            db.close()
            client.close()
            return jsonify({'message': 'Only Acting Admin can mark attendance'}), 403

        # Get employee details using emp_no
        db.execute("""
            SELECT e.*, c.company_name 
            FROM employees e 
            JOIN companies c ON e.company_name = c.company_name 
            WHERE e.emp_no = %s
        """, (data['id'],))  # We're using emp_no but passing it as id
        employee = db.fetchone()
        
        if not employee:
            db.close()
            client.close()
            return jsonify({'message': f"Employee {data['id']} not found"}), 404

        # Generate check-in and check-out times
        current_time = datetime.now()
        checkin = current_time
        # Add 8 hours for check-out time
        checkout = checkin + timedelta(hours=8)

        # Insert attendance record
        db.execute("""
            INSERT INTO attendance (
                emp_no, employee_id, company_name, shift_start_time, shift_end_time
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """, (
            employee['emp_no'],
            employee['id'],
            employee['company_name'],
            checkin.time(),
            checkout.time()
        ))

        client.commit()
        db.close()
        client.close()

        return jsonify({
            'message': 'Attendance marked successfully',
            'emp_no': employee['emp_no'],
            'employee_id': employee['id'],
            'company_name': employee['company_name'],
            'shift_start_time': checkin.time().strftime('%H:%M:%S'),
            'shift_end_time': checkout.time().strftime('%H:%M:%S')
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Unexpected error: {str(e)}'}), 500

@attendance_bp.route('/checkin', methods=['POST'])
def checkin():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization token is missing'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_emp_no = payload.get('emp_no')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if current user is Acting Admin
        db.execute("SELECT role FROM employees WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()
        if not current_user or current_user['role'] != 'Acting Admin':
            db.close()
            client.close()
            return jsonify({'message': 'Only Acting Admin can mark attendance'}), 403

        # Get employee number to mark (from request or current user)
        data = request.get_json() or {}
        emp_no = data.get('emp_no', current_user_emp_no)

        # Check if user exists
        db.execute("""
            SELECT e.*, c.company_name 
            FROM employees e 
            JOIN companies c ON e.company_name = c.company_name 
            WHERE e.emp_no = %s
        """, (emp_no,))
        user = db.fetchone()
        if not user:
            db.close()
            client.close()
            return jsonify({'message': 'User not found'}), 404

        # Check if already checked in today
        current_date = datetime.now().date()
        db.execute("""
            SELECT * FROM attendance 
            WHERE emp_no = %s AND date = %s AND checkin_time IS NOT NULL AND checkout_time IS NULL
        """, (emp_no, current_date))
        existing_attendance = db.fetchone()
        
        if existing_attendance:
            db.close()
            client.close()
            return jsonify({'message': f'User {emp_no} has already checked in today'}), 400

        # Mark check-in
        checkin_time = datetime.now()
        # Add 8 hours for check-out time
        checkout_time = checkin_time + timedelta(hours=8)
        db.execute("""
            INSERT INTO attendance (
                emp_no, id, name, company_name, checkin_time, checkout_time, date, status, marked_by
            ) VALUES (
                %s, 
                %s,
                %s,
                %s,
                %s, 
                %s, 
                %s, 
                'Active',
                %s
            )
        """, (
            emp_no,
            user['id'],
            user['name'],
            user['company_name'],
            checkin_time,
            checkout_time,
            current_date,
            current_user_emp_no
        ))
        
        client.commit()
        db.close()
        client.close()

        return jsonify({
            'message': 'Check-in successful',
            'emp_no': emp_no,
            'name': user['name'],
            'company_name': user['company_name'],
            'checkin_time': checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
            'checkout_time': checkout_time.strftime('%Y-%m-%d %H:%M:%S')
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Unexpected error: {str(e)}'}), 500

@attendance_bp.route('/checkout', methods=['POST'])
def checkout():
    try:
        # Verify token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization token is missing'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
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

        # Check if current user is Acting Admin
        db.execute("SELECT role FROM employees WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()
        if not current_user or current_user['role'] != 'Acting Admin':
            db.close()
            client.close()
            return jsonify({'message': 'Only Acting Admin can mark attendance'}), 403

        # Get employee number to mark (from request or current user)
        data = request.get_json() or {}
        emp_no = data.get('emp_no', current_user_emp_no)

        # Check if user exists
        db.execute("SELECT * FROM employees WHERE emp_no = %s", (emp_no,))
        user = db.fetchone()
        if not user:
            db.close()
            client.close()
            return jsonify({'message': 'User not found'}), 404

        # Check for an active check-in today
        current_date = datetime.now().date()
        db.execute("""
            SELECT * FROM attendance 
            WHERE emp_no = %s AND date = %s AND checkin_time IS NOT NULL AND checkout_time IS NULL
        """, (emp_no, current_date))
        existing_attendance = db.fetchone()
        
        # Debug logging
        if not existing_attendance:
            # Additional query to understand the current state
            db.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN checkin_time IS NOT NULL THEN 1 ELSE 0 END) as checkin_count,
                    SUM(CASE WHEN checkout_time IS NOT NULL THEN 1 ELSE 0 END) as checkout_count
                FROM attendance 
                WHERE emp_no = %s AND date = %s
            """, (emp_no, current_date))
            attendance_stats = db.fetchone()

            print(f"Attendance Debug for {emp_no} on {current_date}:")
            print(f"Total Records: {attendance_stats['total_records']}")
            print(f"Check-in Count: {attendance_stats['checkin_count']}")
            print(f"Check-out Count: {attendance_stats['checkout_count']}")

            db.close()
            client.close()
            return jsonify({
                'message': f'No active check-in found for user {emp_no} today',
                'debug': {
                    'total_records': attendance_stats['total_records'],
                    'checkin_count': attendance_stats['checkin_count'],
                    'checkout_count': attendance_stats['checkout_count']
                }
            }), 400

        # Calculate total hours
        checkout_time = datetime.now()
        checkin_time = existing_attendance['checkin_time']
        total_hours = (checkout_time - checkin_time).total_seconds() / 3600
        adjusted_hours = min(total_hours, 8.0)  # Cap at 8 hours

        # Update attendance with checkout
        db.execute("""
            UPDATE attendance 
            SET checkout_time = %s, 
                total_hours = %s, 
                status = 'Completed',
                marked_by = %s
            WHERE emp_no = %s AND date = %s AND checkin_time IS NOT NULL AND checkout_time IS NULL
        """, (checkout_time, round(adjusted_hours, 2), current_user_emp_no, emp_no, current_date))
        
        client.commit()
        db.close()
        client.close()

        return jsonify({
            'message': 'Check-out successful', 
            'emp_no': emp_no,
            'checkout_time': checkout_time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_hours': round(adjusted_hours, 2)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Unexpected error: {str(e)}'}), 500

@attendance_bp.route('/status', methods=['GET'])
def check_attendance_status():
    try:
        # Verify token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization token is missing'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            emp_no = payload.get('emp_no')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        # Connect to database
        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if user exists
        db.execute("SELECT * FROM employees WHERE emp_no = %s", (emp_no,))
        user = db.fetchone()
        if not user:
            db.close()
            client.close()
            return jsonify({'message': 'User not found'}), 404

        # Check current attendance status
        current_date = datetime.now().date()
        db.execute("""
            SELECT checkin_time, checkout_time, status 
            FROM attendance 
            WHERE emp_no = %s AND date = %s
            ORDER BY checkin_time DESC
            LIMIT 1
        """, (emp_no, current_date))
        attendance_record = db.fetchone()

        db.close()
        client.close()

        if not attendance_record:
            return jsonify({
                'message': 'No attendance record for today',
                'can_checkin': True,
                'can_checkout': False
            }), 200

        # Determine attendance status
        if attendance_record['checkin_time'] and not attendance_record['checkout_time']:
            return jsonify({
                'message': 'Checked in today',
                'checkin_time': attendance_record['checkin_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'can_checkin': False,
                'can_checkout': True,
                'status': attendance_record['status']
            }), 200

        if attendance_record['checkin_time'] and attendance_record['checkout_time']:
            return jsonify({
                'message': 'Checked out today',
                'checkin_time': attendance_record['checkin_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'checkout_time': attendance_record['checkout_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'can_checkin': False,
                'can_checkout': False,
                'status': attendance_record['status']
            }), 200

        # Fallback
        return jsonify({
            'message': 'Unexpected attendance status',
            'can_checkin': True,
            'can_checkout': False
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Unexpected error: {str(e)}'}), 500
