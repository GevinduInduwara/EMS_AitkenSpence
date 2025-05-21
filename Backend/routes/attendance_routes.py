from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2 import extras, sql
import os
import traceback
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import jwt
from models import get_db_connection, close_db_connection, mark_attendance

load_dotenv()
attendance_bp = Blueprint('attendance', __name__)

# Debug route to test if the blueprint is working
@attendance_bp.route('/debug', methods=['GET'])
def debug_route():
    return jsonify({
        'message': 'Attendance routes are working!',
        'current_time': datetime.now().isoformat()
    }), 200

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:Gevindu@localhost:5433/Security-Attendance")

# Assuming SECRET_KEY is defined elsewhere in the code
SECRET_KEY = os.getenv("SECRET_KEY")

# Default shift times (can be customized)
DEFAULT_SHIFT_START = time(8, 0)  # 8:00 AM
DEFAULT_SHIFT_END = time(17, 0)    # 5:00 PM

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

        # Check if current user has permission (Admin or Acting Admin)
        db.execute("SELECT role FROM employees WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()

        if not current_user or current_user['role'].lower() not in ['admin', 'acting_admin']:
            db.close()
            client.close()
            return jsonify({'message': 'Only Admin or Acting Admin can mark attendance'}), 403

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
            checkin,
            checkout
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

@attendance_bp.route('/records', methods=['GET'])
def get_attendance_records():
    try:
        emp_no = request.args.get('emp_no')
        if not emp_no:
            return jsonify({'success': False, 'message': 'emp_no query parameter is required'}), 400

        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        db.execute("""
            SELECT id, emp_no, shift_start_time, shift_end_time
            FROM attendance
            WHERE emp_no = %s
            ORDER BY shift_start_time DESC
        """, (emp_no,))
        records = db.fetchall()
        db.close()
        client.close()

        records_list = [
            {
                'id': r['id'],
                'emp_no': r['emp_no'],
                'shift_start_time': r['shift_start_time'].isoformat() if r['shift_start_time'] else None,
                'shift_end_time': r['shift_end_time'].isoformat() if r['shift_end_time'] else None,
                'status': 'IN' if r['shift_end_time'] is None else 'OUT'
            }
            for r in records
        ]

        return jsonify({'success': True, 'records': records_list}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error fetching records: {str(e)}'}), 500


@attendance_bp.route('/records/<int:record_id>', methods=['PUT'])
def update_attendance_record(record_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Authorization token is missing'}), 401
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        data = request.get_json()
        shift_start_time = data.get('shift_start_time')
        shift_end_time = data.get('shift_end_time')
        status = data.get('status')
        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)
        db.execute("""
            UPDATE attendance
            SET shift_start_time = %s,
                shift_end_time = %s,
                status = %s
            WHERE id = %s
            RETURNING id, emp_no, shift_start_time, shift_end_time, status
        """, (shift_start_time, shift_end_time, status, record_id))
        updated = db.fetchone()
        client.commit()
        db.close()
        client.close()
        if not updated:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        return jsonify({'success': True, 'record': dict(updated)}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error updating record: {str(e)}'}), 500

@attendance_bp.route('/checkin', methods=['POST'])
def checkin():
    try:
        # Verify token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Authorization token is missing'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_emp_no = payload.get('emp_no')
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401

        # Connect to database
        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if current user is Acting Admin
        db.execute("SELECT role FROM employees WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()
        # Debug: print the current user and role
        print(f"[DEBUG] JWT payload: {payload if 'payload' in locals() else 'N/A'}")
        print(f"[DEBUG] Current user from DB: {current_user}")
        if not current_user or current_user['role'].lower() not in ['admin', 'acting_admin']:
            db.close()
            client.close()
            return jsonify({'success': False, 'message': 'Only admin or acting_admin can mark attendance'}), 403

        # Get employee number to mark
        data = request.get_json() or {}
        emp_no = data.get('emp_no')
        
        if not emp_no:
            db.close()
            client.close()
            return jsonify({'success': False, 'message': 'Employee number is required'}), 400

        # Get employee details
        db.execute("""
            SELECT e.*, c.company_name 
            FROM employees e 
            LEFT JOIN companies c ON e.company_name = c.company_name 
            WHERE e.emp_no = %s
        """, (emp_no,))
        user = db.fetchone()
        if not user:
            db.close()
            client.close()
            return jsonify({'success': False, 'message': 'Employee not found'}), 404

        current_date = datetime.now().date()
        current_time = datetime.now()

        # Check if already checked in today
        db.execute("""
            SELECT * FROM attendance 
            WHERE emp_no = %s AND updated_at::date = %s AND shift_end_time IS NULL
            ORDER BY shift_start_time DESC
            LIMIT 1
        """, (emp_no, current_date))
        
        existing_attendance = db.fetchone()
        if existing_attendance:
            db.close()
            client.close()
            return jsonify({
                'success': False,
                'message': f'Employee {emp_no} has an active session. Please check out first.'
            }), 400

        try:
            # Mark check-in
            current_time = datetime.now()
            shift_start_time = current_time  # Use datetime, not .time()
            shift_end_time = None  # set to NULL in the database
            db.execute("""
                INSERT INTO attendance (
                    emp_no, employee_id, company_name, 
                    shift_start_time, shift_end_time, updated_at
                ) VALUES (
                    %s, %s, %s, 
                    %s, %s, %s
                )
                RETURNING id, shift_start_time, shift_end_time
            """, (
                emp_no,
                user.get('id'),
                user.get('company_name'),
                shift_start_time,
                shift_end_time,
                current_time
            ))
            
            # Get the inserted record
            attendance_id = db.fetchone()['id']
            
            # Update the checkout time to be 8 hours after check-in
            client.commit()
            return jsonify({
                'success': True,
                'data': {
                    'name': user.get('name'),
                    'checkin_time': shift_start_time.isoformat(),
                    'checkout_time': None
                }
            }), 200
            
        except Exception as e:
            client.rollback()
            raise e
            
        finally:
            db.close()
            client.close()

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
            return jsonify({'success': False, 'message': 'Authorization token is missing'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_emp_no = payload.get('emp_no')
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401

        # Connect to database
        client = psycopg2.connect(database_url)
        db = client.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if current user is Acting Admin
        db.execute("SELECT role FROM employees WHERE emp_no = %s", (current_user_emp_no,))
        current_user = db.fetchone()
        # Debug: print the current user and role
        print(f"[DEBUG] JWT payload: {payload if 'payload' in locals() else 'N/A'}")
        print(f"[DEBUG] Current user from DB: {current_user}")
        if not current_user or current_user['role'].lower() not in ['admin', 'acting_admin']:
            db.close()
            client.close()
            return jsonify({'success': False, 'message': 'Only admin or acting_admin can mark attendance'}), 403

        # Get employee number to mark
        data = request.get_json() or {}
        emp_no = data.get('emp_no')
        
        if not emp_no:
            db.close()
            client.close()
            return jsonify({'success': False, 'message': 'Employee number is required'}), 400

        # Get employee details
        db.execute("""
            SELECT e.*, c.company_name 
            FROM employees e 
            LEFT JOIN companies c ON e.company_name = c.company_name 
            WHERE e.emp_no = %s
        """, (emp_no,))
        
        user = db.fetchone()
        if not user:
            db.close()
            client.close()
            return jsonify({'success': False, 'message': 'Employee not found'}), 404

        current_date = datetime.now().date()
        current_time = datetime.now()

        # Check if user has an active check-in
        db.execute("""
            SELECT * FROM attendance 
            WHERE emp_no = %s AND updated_at::date = %s AND shift_end_time IS NULL
            ORDER BY shift_start_time DESC
            LIMIT 1
        """, (emp_no, current_date))
        
        attendance_record = db.fetchone()
        if not attendance_record:
            db.close()
            client.close()
            return jsonify({
                'success': False,
                'message': f'No active check-in found for employee {emp_no}'
            }), 400

        try:
            # Calculate work hours
            shift_start_time = attendance_record['shift_start_time']
            # Ensure both are datetime, not time
            if isinstance(shift_start_time, time):
                # Convert to today's datetime for compatibility (should not happen with new schema)
                shift_start_time = datetime.combine(current_time.date(), shift_start_time)
            work_hours = (current_time - shift_start_time).total_seconds() / 3600  # in hours
            
            # Update the attendance record with checkout time
            db.execute("""
                UPDATE attendance 
                SET shift_end_time = %s,

                    updated_at = CURRENT_TIMESTAMP,
                    total_work_hours = %s * INTERVAL '1 hour',
                    shift_count = CEIL(EXTRACT(EPOCH FROM (%s - shift_start_time)) / (12 * 60 * 60))
                WHERE id = %s
                RETURNING *
            """, (current_time, work_hours, current_time, attendance_record['id']))
            
            updated_record = db.fetchone()
            
            client.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'name': user.get('name'),
                    'checkin_time': shift_start_time.isoformat() if shift_start_time else None,
                    'checkout_time': updated_record['shift_end_time'].isoformat() if updated_record['shift_end_time'] else None,
                    'total_work_hours': str(updated_record['total_work_hours'])
                }
            }), 200
            
        except Exception as e:
            client.rollback()
            raise e
            
        finally:
            db.close()
            client.close()

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
            SELECT shift_start_time, shift_end_time, status 
            FROM attendance 
            WHERE emp_no = %s AND date = %s
            ORDER BY shift_start_time DESC
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
        if attendance_record['shift_start_time'] and not attendance_record['shift_end_time']:
            return jsonify({
                'message': 'Checked in today',
                'shift_start_time': attendance_record['shift_start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'can_checkin': False,
                'can_checkout': True,
                'status': attendance_record['status']
            }), 200

        if attendance_record['shift_start_time'] and attendance_record['shift_end_time']:
            return jsonify({
                'message': 'Checked out today',
                'shift_start_time': attendance_record['shift_start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'shift_end_time': attendance_record['shift_end_time'].strftime('%Y-%m-%d %H:%M:%S'),
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
