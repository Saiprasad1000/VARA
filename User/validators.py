import re
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from PIL import Image

User = get_user_model()

def validate_name(name):
    if not name.isalpha():
        raise ValidationError("Name should contain only letters.")

def validate_email_unique(email):
    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already registered.")

def validate_mobile(mobile):
    if not re.match(r'^\d{10}$', mobile):
        raise ValidationError("Mobile number must be 10 digits.")
    if User.objects.filter(mobile=mobile).exists():
        raise ValidationError("Mobile number already registered.")

def validate_password_strength(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character.")

def validate_password_match(password, confirm_password):
    if password != confirm_password:
        raise ValidationError("Passwords do not match.")
    
def validate_image(file):
    try:
        img = Image.open(file)
        img.verify()  # Verify that it's an image
    except Exception:
        raise ValidationError("Uploaded file is not a valid image.")

