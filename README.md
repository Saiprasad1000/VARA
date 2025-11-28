# VARA - Art E-commerce Platform

A Django-based e-commerce platform for buying and selling paintings.

## Features

- User authentication with email verification (OTP)
- Google OAuth integration
- Product management (CRUD operations)
- Category management
- Image upload and processing
- Admin dashboard
- Customer management
- Offers and discounts
- Redis caching for sessions and OTP storage
- Celery for asynchronous email tasks

## Prerequisites

- Python 3.10+
- PostgreSQL
- Redis Server

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Vara
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv varavenv
   # On Windows
   varavenv\Scripts\activate
   # On Linux/Mac
   source varavenv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your configuration values:
     ```
     SECRET_KEY=your-secret-key
     DEBUG=True
     DB_NAME=vara_db
     DB_USER=postgres
     DB_PASSWORD=your-password
     DB_HOST=localhost
     DB_PORT=5432
     EMAIL_HOST_USER=your-email@gmail.com
     EMAIL_HOST_PASSWORD=your-app-password
     ```

5. **Create PostgreSQL database**
   ```sql
   CREATE DATABASE vara_db;
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start Redis server**
   ```bash
   redis-server
   ```

9. **Start Celery worker** (in a new terminal)
   ```bash
   celery -A Vara worker -l info
   ```

10. **Run development server**
    ```bash
    python manage.py runserver
    ```

## Project Structure

```
Vara/
├── Admin/              # Admin app for backend management
├── User/               # User app for authentication and frontend
├── Vara/               # Main project settings
├── media/              # User uploaded files
├── staticfiles/        # Collected static files
└── manage.py
```

## Usage

- **User Interface**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **Django Admin**: http://localhost:8000/admins/

## Technologies Used

- Django 5.x
- PostgreSQL
- Redis
- Celery
- Django Allauth (Google OAuth)
- Pillow (Image processing)
- django-redis

## License

MIT License
