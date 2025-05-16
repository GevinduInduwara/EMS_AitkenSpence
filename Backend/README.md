# Security Attendance App Backend

## Overview
A Flask-based backend for a Security Attendance Tracking System.

## Features
- User Registration
- User Authentication
- Attendance Check-in/Check-out
- Attendance History

## Prerequisites
- Python 3.8+
- PostgreSQL
- pip

## Setup
1. Clone the repository
2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database
- Create a database named `Security-Attendance`
- Update database connection in `.env`

5. Create database tables
```bash
python models.py
```

6. Run the application
```bash
python app.py
```

## Environment Variables
Create a `.env` file with:
```
DATABASE_URL=postgresql://username:password@localhost:5432/Security-Attendance
SECRET_KEY=your_secret_key
DEBUG=True
```

## API Endpoints
- `/api/users/register`: Register a new user
- `/api/users/login`: User login
- `/api/users/attendance/checkin`: Check-in
- `/api/users/attendance/checkout`: Check-out
- `/api/users/attendance/history`: View attendance history

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
