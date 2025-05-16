import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv()

def create_db_pool():
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5433'),
            'database': os.getenv('DB_NAME', 'Security-Attendance'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'Gevindu')
        }
        
        # Create connection pool
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # minconn
            10, # maxconn
            **db_config
        )
        
        # Get a connection to set auto-commit for schema changes
        conn = connection_pool.getconn()
        conn.autocommit = True
        connection_pool.putconn(conn)
        
        return connection_pool
    except Exception as e:
        print(f"Error creating connection pool: {e}")
        raise

# Create global connection pool
connection_pool = create_db_pool()

def get_db_connection():
    try:
        conn = connection_pool.getconn()
        # For schema changes, enable autocommit
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error getting connection: {e}")
        raise

def close_db_connection(conn):
    try:
        connection_pool.putconn(conn)
    except Exception as e:
        print(f"Error returning connection: {e}")
        raise
