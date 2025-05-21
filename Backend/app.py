import os
import signal
import warnings
import psycopg2
from psycopg2 import extras, sql
from datetime import datetime, timedelta
import bcrypt
import jwt
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from routes.user_routes import user_bp
from routes.attendance_routes import attendance_bp
from routes.company_routes import company_bp
from dotenv import load_dotenv
from models import initialize_database, get_db_connection, close_db_connection

# Suppress the semaphore warnings
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be \\d+ leaked semaphore objects to clean up at shutdown")

load_dotenv()

app = Flask(__name__)

# Test route to verify the Flask app is working
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'success',
        'message': 'Flask app is running!',
        'time': datetime.now().isoformat()
    })

# Allow requests from localhost and your local network IP
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:19006",  # Expo web
            "http://localhost:5001",   # Local development
            "http://localhost:5002",   # New port
            "http://172.20.10.3:5001", # Your local network IP
            "http://172.20.10.3:5002", # New port
            "http://192.168.1.100:5001",
            "http://192.168.1.100:5002",
            "http://192.168.1.100:8081"
        ],
        "supports_credentials": True
    }
})

def apply_migrations():
    """Apply database migrations from the migrations directory."""
    print("Checking for database migrations...")
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    if not os.path.exists(migrations_dir):
        print("No migrations directory found. Skipping migrations.")
        return
    
    migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
    
    if not migration_files:
        print("No migration files found in migrations directory.")
        return
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create migrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get applied migrations
        cursor.execute("SELECT filename FROM migrations")
        applied_migrations = {row[0] for row in cursor.fetchall()}
        
        # Apply new migrations
        for filename in migration_files:
            if filename not in applied_migrations:
                print(f"Applying migration: {filename}")
                with open(os.path.join(migrations_dir, filename), 'r') as f:
                    sql_script = f.read()
                    cursor.execute(sql_script)
                
                # Record the migration
                cursor.execute(
                    "INSERT INTO migrations (filename) VALUES (%s) ON CONFLICT (filename) DO NOTHING",
                    (filename,)
                )
                conn.commit()
                print(f"Successfully applied migration: {filename}")
        
        print("Database migrations completed successfully!")
        
    except Exception as e:
        print(f"Error applying migrations: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)

# Initialize database and apply migrations when app starts
with app.app_context():
    try:
        initialize_database()
        apply_migrations()
        print("Database initialization and migrations completed successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        
# Debug: Print all registered routes before adding blueprints
print("\nBefore registering blueprints:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")

# Register blueprints with proper URL prefixes
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
app.register_blueprint(company_bp, url_prefix='/api/company')

# Debug: Print all registered routes after adding blueprints
print("\nAfter registering blueprints:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route('/shutdown', methods=['POST'])
def shutdown():
    return shutdown_server()

def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    # Add any cleanup code here if needed
    os._exit(0)

def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination
    
    # Configuration
    port = int(os.getenv("PORT", "5001"))  # Default port changed to 5001
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    
    try:
        print(f"Starting server on {host}:{port} (debug={debug})...")
        app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    finally:
        print("Server has been stopped")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
