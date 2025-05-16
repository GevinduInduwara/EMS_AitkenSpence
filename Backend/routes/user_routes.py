from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from models import (
    get_db_connection, close_db_connection, hash_password, verify_password,
    get_all_employees, get_employees_by_rank, get_employee_by_emp_no
)
import jwt
from datetime import datetime, timedelta
import os

user_bp = Blueprint('user', __name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:Gevindu@localhost:5433/Security-Attendance")

@user_bp.route('/login', methods=['POST'])
@cross_origin()
def login():
    try:
        data = request.get_json()
        print('Login attempt received for emp_no:', data.get('emp_no'))
        
        emp_no = data.get('emp_no')
        password = data.get('password')

        if not emp_no or not password:
            return jsonify({'message': 'Employee number and password are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT emp_no, name, role, tel, 
                   security_firm, rank, password, company_name
            FROM employees 
            WHERE emp_no = %s
        """
        cursor.execute(query, (emp_no,))
        employee = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)

        if not employee:
            return jsonify({'message': 'Employee not found or not authorized to log in'}), 404

        if len(employee) < 8:
            return jsonify({'message': f'Internal error: employee tuple too short ({len(employee)})'}), 500

        if employee[6] is None:
            return jsonify({'message': 'Internal error: password is None'}), 500

        is_valid = verify_password(employee[6], password)
        if not is_valid:
            return jsonify({'message': 'Invalid credentials'}), 401

        role = employee[2].strip().lower() if employee[2] else ''
        if role not in ['admin', 'acting admin', 'user']:
            return jsonify({'message': 'Role must be either admin, Acting Admin, or user', 'role': employee[2]}), 403

        token = jwt.encode({
            'emp_no': employee[0],
            'role': employee[2],
            'rank': employee[5],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')

        response_data = {
            'token': token,
            'role': employee[2],
            'rank': employee[5],
            'name': employee[1],
            'emp_no': employee[0],
            'company_name': employee[7]
        }
        return jsonify(response_data), 200

    except Exception as e:
        import traceback
        return jsonify({'message': f'Error during login: {str(e)}', 'trace': traceback.format_exc()}), 500

@user_bp.route('/employees_by_rank', methods=['GET'])
@cross_origin()
def employees_by_rank():
    rank = request.args.get('rank')
    if not rank:
        return jsonify({'message': 'Rank is required as a query parameter'}), 400
    try:
        employees = get_employees_by_rank(rank)
        return jsonify({
            'message': f'Employees with rank {rank} retrieved successfully',
            'employees': employees
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error retrieving employees by rank: {str(e)}'}), 500

@user_bp.route('/employee/<string:emp_no>', methods=['GET'])
@cross_origin()
def get_employee(emp_no):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT e.*, c.company_name 
            FROM employees e 
            JOIN companies c ON e.company_name = c.company_name 
            WHERE e.emp_no = %s
        """
        cursor.execute(query, (emp_no,))
        employee = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        if not employee:
            return jsonify({'message': 'Employee not found'}), 404
            
        return jsonify(dict(employee)), 200
    except Exception as e:
        return jsonify({'message': f'Error retrieving employee: {str(e)}'}), 500

@user_bp.route('/employee/add', methods=['POST'])
@cross_origin()
def add_employee():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['emp_no', 'id', 'name', 'role', 'tel', 'company_name', 'security_firm', 'rank', 'password', 'nic']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'All fields are required'}), 400

        # Get database connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if company exists and create if it doesn't
        cursor.execute("""
            SELECT 1 FROM companies WHERE company_name = %s
        """, (data['company_name'],))
        
        if not cursor.fetchone():
            # Create the company
            cursor.execute("""
                INSERT INTO companies (company_name, address, subsidiary, contact_number)
                VALUES (%s, %s, %s, %s)
            """, (
                data['company_name'],
                data.get('address', None),
                data['security_firm'],
                data['tel']
            ))
        
        # Check if employee already exists
        cursor.execute("""
            SELECT 1 FROM employees WHERE emp_no = %s
        """, (data['emp_no'],))
        
        if cursor.fetchone():
            cursor.close()
            close_db_connection(conn)
            return jsonify({'message': 'Employee already exists'}), 400

        # Hash the password
        hashed_password = hash_password(data['password'])

        # Insert new employee
        cursor.execute("""
            INSERT INTO employees (
                emp_no, id, rank, name, tel, company_name, 
                address, nic, password, security_firm, role
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['emp_no'],
            data['id'],
            data['rank'],
            data['name'],
            data['tel'],
            data['company_name'],
            data.get('address', None),
            data['nic'],
            hashed_password,
            data['security_firm'],
            data['role']
        ))
        
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        return jsonify({
            'message': 'Employee added successfully', 
            'emp_no': data['emp_no']
        }), 201

    except Exception as e:
        if 'conn' in locals():
            try:
                cursor.close()
            except:
                pass
            try:
                close_db_connection(conn)
            except:
                pass
        
        print(f"Error adding employee: {e}")
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500

@user_bp.route('/employee/<emp_no>', methods=['GET'])
@cross_origin()
def get_employee_by_emp_no_route(emp_no):
    try:
        employee = get_employee_by_emp_no(emp_no)
        if not employee:
            return jsonify({'message': 'Employee not found'}), 404

        return jsonify({
            'emp_no': employee[0],
            'name': employee[1],
            'role': employee[2],
            'tel': employee[3],
            'company_name': employee[4],
            'security_firm': employee[5],
            'rank': employee[6]
        }), 200

    except Exception as e:
        return jsonify({'message': f'Error retrieving employee: {str(e)}'}), 500
