from flask import Blueprint, jsonify, request
from models import get_db_connection, close_db_connection

company_bp = Blueprint('company', __name__)

@company_bp.route('/company/add', methods=['POST'])
def add_company():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['company_name', 'address', 'subsidiary', 'contact_number']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'All fields are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if company already exists
        cursor.execute("""
            SELECT * FROM companies 
            WHERE company_name = %s
        """, (data['company_name'],))
        
        if cursor.fetchone():
            cursor.close()
            close_db_connection(conn)
            return jsonify({'message': 'Company already exists'}), 400

        # Insert new company
        cursor.execute("""
            INSERT INTO companies (company_name, address, subsidiary, contact_number)
            VALUES (%s, %s, %s, %s)
        """, (
            data['company_name'], 
            data['address'],
            data['subsidiary'],
            data['contact_number']
        ))
        
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        return jsonify({
            'message': 'Company added successfully', 
            'company_name': data['company_name']
        }), 201

    except Exception as e:
        # Ensure database connections are closed in case of an error
        if 'conn' in locals():
            try:
                cursor.close()
            except:
                pass
            try:
                close_db_connection(conn)
            except:
                pass
        
        print(f"Error adding company: {e}")
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500

@company_bp.route('/company/all', methods=['GET'])
def get_all_companies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, company_name FROM companies
        """)
        
        companies = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        
        return jsonify([{
            'id': company['id'],
            'company_name': company['company_name']
        } for company in companies]), 200
        
    except Exception as e:
        return jsonify({'message': f"Error occurred: {str(e)}"}), 500

@company_bp.route('/company/list', methods=['GET'])
def get_all_companies_list():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company_name, address, subsidiary, contact_number 
            FROM companies 
            ORDER BY company_name
        """)
        companies = cursor.fetchall()

        cursor.close()
        close_db_connection(conn)

        companies_data = [dict(company) for company in companies]

        return jsonify({
            'message': 'Companies retrieved successfully',
            'companies': companies_data
        }), 200

    except Exception as e:
        # Ensure database connections are closed in case of an error
        if 'conn' in locals():
            cursor.close()
            close_db_connection(conn)
        
        print(f"Error retrieving companies: {e}")
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500

@company_bp.route('/company/<string:company_name>', methods=['GET'])
def get_company(company_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company_name, address, subsidiary, contact_number 
            FROM companies 
            WHERE company_name = %s
        """, (company_name,))
        company = cursor.fetchone()
        
        cursor.close()
        close_db_connection(conn)

        if not company:
            return jsonify({'message': f'Company {company_name} not found'}), 404

        company_data = dict(company)

        return jsonify({
            'message': 'Company retrieved successfully',
            'company': company_data
        }), 200

    except Exception as e:
        # Ensure database connections are closed in case of an error
        if 'conn' in locals():
            cursor.close()
            close_db_connection(conn)
        
        print(f"Error retrieving company: {e}")
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500

@company_bp.route('/company/<string:company_name>', methods=['PUT'])
def update_company(company_name):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No update fields provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if company exists
        cursor.execute("SELECT 1 FROM companies WHERE company_name = %s", (company_name,))
        if not cursor.fetchone():
            cursor.close()
            close_db_connection(conn)
            return jsonify({'message': f'Company {company_name} not found'}), 404

        # Prepare update fields
        update_fields = []
        params = []

        if 'address' in data:
            update_fields.append("address = %s")
            params.append(data['address'])

        if 'subsidiary' in data:
            update_fields.append("subsidiary = %s")
            params.append(data['subsidiary'])

        if 'contact_number' in data:
            update_fields.append("contact_number = %s")
            params.append(data['contact_number'])

        # If no fields to update
        if not update_fields:
            cursor.close()
            close_db_connection(conn)
            return jsonify({'message': 'No valid update fields provided'}), 400

        # Add company_name to params
        params.append(company_name)

        # Construct and execute update query
        update_query = f"""
            UPDATE companies 
            SET {', '.join(update_fields)}
            WHERE company_name = %s
        """
        cursor.execute(update_query, params)
        conn.commit()

        cursor.close()
        close_db_connection(conn)

        return jsonify({
            'message': 'Company updated successfully',
            'company_name': company_name
        }), 200

    except Exception as e:
        # Ensure database connections are closed in case of an error
        if 'conn' in locals():
            cursor.close()
            close_db_connection(conn)
        
        print(f"Error updating company: {e}")
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500

@company_bp.route('/company/<string:company_name>', methods=['DELETE'])
def delete_company(company_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if company exists
        cursor.execute("SELECT * FROM companies WHERE company_name = %s", (company_name,))
        company = cursor.fetchone()

        if not company:
            cursor.close()
            close_db_connection(conn)
            return jsonify({'message': f'Company {company_name} not found'}), 404

        # Delete the company
        cursor.execute("DELETE FROM companies WHERE company_name = %s", (company_name,))
        conn.commit()

        cursor.close()
        close_db_connection(conn)

        return jsonify({
            'message': 'Company deleted successfully',
            'company_name': company_name
        }), 200

    except Exception as e:
        # Ensure database connections are closed in case of an error
        if 'conn' in locals():
            cursor.close()
            close_db_connection(conn)
        
        print(f"Error deleting company: {e}")
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500
