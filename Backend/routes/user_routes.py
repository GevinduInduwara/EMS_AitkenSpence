from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import psycopg2
from psycopg2 import extras, errors
import traceback
import os
import traceback
from datetime import datetime, timedelta
import jwt
from models import (
    get_db_connection, close_db_connection, 
    hash_password, verify_password,
    get_all_employees, get_employees_by_rank, 
    get_employee_by_emp_no
)

user_bp = Blueprint('user', __name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:Gevindu@localhost:5433/Security-Attendance")

@user_bp.route('/login', methods=['POST'])
@cross_origin()
def login():
    conn = None
    cursor = None
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        emp_no = data.get('emp_no')
        password = data.get('password')
        
        # Validate input
        if not emp_no or not password:
            return jsonify({'message': 'Employee number and password are required'}), 400

        # Get database connection
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=extras.DictCursor)
            
            # Query employee
            query = """
                SELECT emp_no, name, role, tel, 
                       security_firm, rank, password, company_name
                FROM employees 
                WHERE emp_no = %s
            """
            cursor.execute(query, (emp_no,))
            employee = cursor.fetchone()
            
            if not employee:
                return jsonify({'message': 'Invalid credentials'}), 401
                
            # Verify password
            if not employee.get('password'):
                return jsonify({'message': 'Authentication error'}), 500
                
            if not verify_password(employee['password'], password):
                return jsonify({'message': 'Invalid credentials'}), 401
                
            # Prepare user data
            user_data = {
                'emp_no': employee['emp_no'],
                'name': employee['name'],
                'role': employee['role'],
                'rank': employee.get('rank', ''),
                'company_name': employee.get('company_name', '')
            }
            
            # Generate token
            token = jwt.encode({
                'emp_no': employee['emp_no'],
                'role': employee['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, SECRET_KEY, algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user_data
            }), 200
            
        except Exception as e:
            print(f"Error during login: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'message': 'Authentication failed'}), 500
            
    except Exception as e:
        print(f"Unexpected error in login: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'message': 'An unexpected error occurred'}), 500
        
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)

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
    conn = None
    cursor = None
    try:
        print(f"Received request for employee: {emp_no}")
        
        # Validate input
        if not emp_no:
            print("Error: Employee number is required")
            return jsonify({'message': 'Employee number is required'}), 400
            
        # Get database connection
        try:
            print("Getting database connection...")
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=extras.DictCursor)
            
            # First, check if the employee exists
            cursor.execute("SELECT 1 FROM employees WHERE emp_no = %s", (emp_no,))
            if not cursor.fetchone():
                print(f"Employee {emp_no} not found")
                return jsonify({'message': 'Employee not found'}), 404
            
            print("Querying employee details...")
            try:
                # Query employee details with a simpler query first
                query = """
                    SELECT emp_no, name, role, tel, 
                           security_firm, rank, company_name
                    FROM employees
                    WHERE emp_no = %s
                """
                print(f"Executing query: {query} with emp_no={emp_no}")
                cursor.execute(query, (emp_no,))
                employee = cursor.fetchone()
                
                if not employee:
                    print("No employee data found after successful existence check")
                    return jsonify({'message': 'Employee data not found'}), 404
                
                print(f"Employee data: {employee}")
                
                # Get company name separately to avoid JOIN issues
                company_name = employee.get('company_name')
                company_display_name = None
                
                if company_name:
                    print(f"Looking up company: {company_name}")
                    try:
                        cursor.execute("SELECT company_name FROM companies WHERE company_name = %s", (company_name,))
                        company = cursor.fetchone()
                        if company:
                            company_display_name = company['company_name']
                            print(f"Found company: {company_display_name}")
                        else:
                            print(f"Company not found: {company_name}")
                    except Exception as e:
                        print(f"Error looking up company: {str(e)}")
                        print(traceback.format_exc())
                else:
                    print("No company name associated with employee")
                
                # Build response with safe attribute access
                employee_data = {
                    'emp_no': employee.get('emp_no'),
                    'name': employee.get('name'),
                    'role': employee.get('role'),
                    'tel': employee.get('tel'),
                    'security_firm': employee.get('security_firm'),
                    'rank': employee.get('rank'),
                    'company_name': company_name,
                    'company_display_name': company_display_name
                }
                print(f"Built employee data: {employee_data}")
                
            except Exception as e:
                print(f"Error in employee data processing: {str(e)}")
                print(traceback.format_exc())
                return jsonify({
                    'message': 'Error processing employee data',
                    'error': str(e),
                    'type': type(e).__name__
                }), 500
            
            print(f"Successfully retrieved employee: {employee_data}")
            return jsonify({
                'message': 'Employee details retrieved successfully',
                'employee': employee_data
            })
            
        except Exception as e:
            error_msg = f"Error retrieving employee: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({
                'message': 'Error retrieving employee details',
                'error': error_msg,
                'type': type(e).__name__
            }), 500
            
    except Exception as e:
        error_msg = f"Unexpected error in get_employee: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            'message': 'An unexpected error occurred',
            'error': error_msg,
            'type': type(e).__name__
        }), 500
        
    finally:
        # Clean up resources
        try:
            if cursor:
                cursor.close()
            if conn:
                close_db_connection(conn)
        except Exception as e:
            print(f"Error cleaning up resources: {str(e)}")

@user_bp.route('/employee/add', methods=['POST'])
@cross_origin()
def add_employee():
    conn = None
    cursor = None
    
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        # Required fields
        required_fields = [
            'emp_no', 'name', 'role', 'tel', 
            'security_firm', 'rank', 'company_name', 
            'nic', 'password'
        ]
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return jsonify({
                'message': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
            
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.DictCursor)
        
        # Check if employee already exists
        cursor.execute("""
            SELECT emp_no, nic 
            FROM employees 
            WHERE emp_no = %s OR nic = %s
        """, (data['emp_no'], data['nic']))
        
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                'message': 'Employee already exists',
                'conflict': 'employee_number' if existing['emp_no'] == data['emp_no'] else 'nic'
            }), 409
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        # Insert new employee
        query = """
            INSERT INTO employees (
                emp_no, name, role, tel, security_firm, 
                rank, company_name, nic, password
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING emp_no, name, role, tel, security_firm, 
                      rank, company_name, nic
        """
        
        cursor.execute(query, (
            data['emp_no'],
            data['name'],
            data['role'],
            data['tel'],
            data['security_firm'],
            data['rank'],
            data['company_name'],
            data['nic'],
            hashed_password
        ))
        
        # Get the newly created employee
        new_employee = cursor.fetchone()
        conn.commit()
        
        # Prepare response
        employee_data = {
            'emp_no': new_employee['emp_no'],
            'name': new_employee['name'],
            'role': new_employee['role'],
            'tel': new_employee['tel'],
            'security_firm': new_employee['security_firm'],
            'rank': new_employee['rank'],
            'company_name': new_employee['company_name'],
            'nic': new_employee['nic']
        }
        
        return jsonify({
            'message': 'Employee added successfully',
            'employee': employee_data
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error adding employee: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'message': 'Error adding employee',
            'error': str(e)
        }), 500
        
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)

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
