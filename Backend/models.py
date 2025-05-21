import psycopg2
from psycopg2 import pool, extras
from dotenv import load_dotenv
import os
import bcrypt
import jwt
import time

load_dotenv()

# Connection settings
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': os.getenv("DB_PORT", "5433"),
    'database': os.getenv("DB_NAME", "Security-Attendance"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "Gevindu"),
    'connect_timeout': 5
}

# Simple connection pool with a fixed size
MAX_CONNECTIONS = 20
connection_pool = None

def get_db_connection():
    """Get a database connection with retry logic."""
    max_retries = 3
    retry_delay = 1
    last_error = None
    
    for attempt in range(max_retries):
        conn = None
        try:
            # Create a new connection
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5433"),
                database=os.getenv("DB_NAME", "Security-Attendance"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "Gevindu"),
                connect_timeout=5
            )
            conn.autocommit = False
            
            # Test the connection
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                
            print(f"Successfully connected to database (attempt {attempt + 1})")
            return conn
            
        except Exception as e:
            last_error = e
            print(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            
            # Clean up any broken connections
            if conn is not None:
                try:
                    if not conn.closed:
                        conn.close()
                except Exception as close_error:
                    print(f"Error closing connection: {str(close_error)}")
            
            if attempt == max_retries - 1:  # Last attempt
                print("Max retries reached, giving up")
                raise Exception(f"Failed to connect to database after {max_retries} attempts. Last error: {str(last_error)}")
                
            # Wait before retrying
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
            
    # This should never be reached due to the raise in the last attempt
    raise Exception("Unexpected error in get_db_connection")

def close_db_connection(conn):
    """Safely close the database connection."""
    if not conn:
        return

    try:
        # Check if the connection is already closed
        if conn.closed:
            print("Connection already closed")
            return
            
        # Try to rollback any pending transactions
        try:
            conn.rollback()
        except Exception as rollback_error:
            print(f"Error during rollback: {str(rollback_error)}")
            
        # Close the connection
        conn.close()
        print("Database connection closed successfully")
        
    except Exception as e:
        print(f"Error closing database connection: {str(e)}")
        
        # If we get here, try a more forceful close
        try:
            if not conn.closed:
                conn.close()
        except Exception as force_close_error:
            print(f"Error during forced connection close: {str(force_close_error)}")

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def get_all_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT emp_no, id, name, role, security_firm, rank
            FROM employees
            ORDER BY emp_no
        """)
        employees = cursor.fetchall()
        return [{
            'emp_no': emp[0],
            'id': emp[1],
            'name': emp[2],
            'role': emp[3],
            'security_firm': emp[4],
            'rank': emp[5]
        } for emp in employees]
    finally:
        cursor.close()
        close_db_connection(conn)

def get_employees_by_rank(rank):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT emp_no, id, name, role, security_firm, rank
            FROM employees
            WHERE rank = %s
            ORDER BY emp_no
        """, (rank,))
        employees = cursor.fetchall()
        return [{
            'emp_no': emp[0],
            'id': emp[1],
            'name': emp[2],
            'role': emp[3],
            'security_firm': emp[4],
            'rank': emp[5]
        } for emp in employees]
    finally:
        cursor.close()
        close_db_connection(conn)

def get_employee_by_id(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT emp_no, name, role, tel, 
                   company_name, security_firm, rank
            FROM employees 
            WHERE id = %s
        """, (employee_id,))
        employee = cursor.fetchone()
        return dict(employee) if employee else None
    except Exception as e:
        print(f"Error fetching employee by ID: {e}")
        return None
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            close_db_connection(conn)

def get_employee_by_nic(nic):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        
        cursor.execute("""
            SELECT emp_no, name, role, department, tel, 
                   company_name, security_firm, rank
            FROM employees 
            WHERE nic = %s
        """, (nic,))
        employee = cursor.fetchone()
        return dict(employee) if employee else None
    except Exception as e:
        print(f"Error fetching employee by NIC: {e}")
        return None
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            close_db_connection(conn)

def get_employee_by_emp_no(emp_no):
    """Get a single employee by employee number."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        
        cursor.execute("""
            SELECT emp_no, name, role, tel, security_firm, rank, company_name
            FROM employees
            WHERE emp_no = %s
        """, (emp_no,))
        
        result = cursor.fetchone()
        return result
        
    except Exception as e:
        print(f"Error in get_employee_by_emp_no: {str(e)}")
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"Error closing cursor: {str(e)}")
        if conn:
            close_db_connection(conn)

def mark_attendance(emp_no, shift_start_time, shift_end_time):
    """Mark attendance with shift times"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if employee exists
        cursor.execute("SELECT emp_no, company_name FROM employees WHERE emp_no = %s", (emp_no,))
        employee = cursor.fetchone()
        
        if not employee:
            print(f"Employee with emp_no {emp_no} not found")
            return False
            
        # Insert attendance record
        cursor.execute("""
            INSERT INTO attendance (
                emp_no, call_date, call_time, status,
                shift_start_time, shift_end_time, company_name
            )
            VALUES (%s, CURRENT_DATE, CURRENT_TIME, 'called', %s, %s, %s)
            RETURNING id
        """, (emp_no, shift_start_time, shift_end_time, employee[1]))
        
        conn.commit()
        attendance_id = cursor.fetchone()[0]
        print(f"Attendance marked successfully for emp_no {emp_no}, record ID: {attendance_id}")
        return True
        
    except Exception as e:
        print(f"Error marking attendance for emp_no {emp_no}: {str(e)}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return False
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            close_db_connection(conn)

def mark_leave(emp_no, leave_type):
    """Mark leave record for an employee"""
    if leave_type not in ['full_day', 'half_day']:
        raise ValueError("Invalid leave type. Must be 'full_day' or 'half_day'")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO attendance (
                emp_no, call_date, call_time, status,
                leave_type, company_name
            )
            SELECT 
                e.emp_no, CURRENT_DATE, CURRENT_TIME, 'leave',
                %s, e.company_name
            FROM employees e
            WHERE e.emp_no = %s
        """, (leave_type, emp_no))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error marking leave: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        close_db_connection(conn)

def get_all_companies():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT company_name, address, subsidiary, contact_number
            FROM companies
            ORDER BY company_name
        """)
        companies = cursor.fetchall()
        return [{
            'company_name': company[0],
            'address': company[1],
            'subsidiary': company[2],
            'contact_number': company[3]
        } for company in companies]
    finally:
        cursor.close()
        close_db_connection(conn)

def initialize_database():
    try:
        # Get connection - auto-commit is enabled in connection pool
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                company_name VARCHAR(100) PRIMARY KEY,
                address VARCHAR(200),
                subsidiary VARCHAR(100),
                contact_number VARCHAR(20),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                emp_no VARCHAR(50) PRIMARY KEY,
                id VARCHAR(20) UNIQUE NOT NULL,
                rank VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                address VARCHAR(200),
                tel VARCHAR(20),
                company_name VARCHAR(100) REFERENCES companies(company_name) ON DELETE CASCADE,
                nic VARCHAR(20) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                security_firm VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                emp_no VARCHAR(50) REFERENCES employees(emp_no) ON DELETE CASCADE,
                employee_id VARCHAR(20) REFERENCES employees(id) ON DELETE CASCADE,
                name VARCHAR(100),
                company_name VARCHAR(100) REFERENCES companies(company_name) ON DELETE CASCADE,
                shift_start_time TIMESTAMP WITH TIME ZONE,
                shift_end_time TIMESTAMP WITH TIME ZONE,
                status VARCHAR(20) DEFAULT 'Active',
                marked_by VARCHAR(50),
                total_work_hours INTERVAL,
                shift_count INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_shift_times CHECK (
                    shift_end_time IS NULL OR shift_end_time > shift_start_time OR 
                    (shift_end_time < shift_start_time AND 
                     (shift_end_time + INTERVAL '24 hours') > shift_start_time)
                )
            );
        """)

        # Create indexes
        cursor.execute("""
            -- Create indexes if they don't exist
            CREATE INDEX IF NOT EXISTS idx_attendance_emp_no ON attendance(emp_no);
            CREATE INDEX IF NOT EXISTS idx_attendance_employee_id ON attendance(employee_id);
        """)

        # Create functions and trigger
        cursor.execute("""
            CREATE OR REPLACE FUNCTION calculate_shift_count(
                start_time TIME,
                end_time TIME
            ) RETURNS INTEGER AS $$
            DECLARE
                total_hours INTERVAL;
                shift_count INTEGER;
            BEGIN
                IF end_time > start_time THEN
                    total_hours := end_time - start_time;
                ELSE
                    total_hours := (end_time + INTERVAL '24 hours') - start_time;
                END IF;
                shift_count := CEIL(EXTRACT(EPOCH FROM total_hours) / (12 * 60 * 60));
                RETURN shift_count;
            END;
            $$ LANGUAGE plpgsql;
        """)

        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_attendance_calculations()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.shift_end_time > NEW.shift_start_time THEN
                    NEW.total_work_hours := NEW.shift_end_time - NEW.shift_start_time;
                ELSE
                    NEW.total_work_hours := (NEW.shift_end_time + INTERVAL '24 hours') - NEW.shift_start_time;
                END IF;
                NEW.shift_count := calculate_shift_count(NEW.shift_start_time, NEW.shift_end_time);
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        cursor.execute("""
            -- Drop existing trigger if it exists
            DROP TRIGGER IF EXISTS update_attendance_calculations ON attendance;
            
            -- Create new trigger
            CREATE TRIGGER update_attendance_calculations
                BEFORE INSERT OR UPDATE ON attendance
                FOR EACH ROW
                EXECUTE FUNCTION update_attendance_calculations();
        """)

        print("Database initialization completed successfully")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)