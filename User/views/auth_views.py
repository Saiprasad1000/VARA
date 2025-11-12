from django.shortcuts import render, redirect
from User.models import CustomUser
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login
from User.tasks import send_welcome_email_task
from User.utilites import generate_otp
from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
import logging
from User.validators import (
    validate_name,
    validate_email_unique,
    validate_mobile,
    validate_password_strength,
    validate_password_match
)


logger = logging.getLogger('django') 


def home(request):
    
    return render(request,'index.html')


def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        referral_code = request.POST.get("referral_code", "")

        try:
            request.session["email"] = email

            # Field-level validation
            validate_name(first_name)
            validate_name(last_name)
            validate_email_unique(email)
            validate_mobile(mobile)
            validate_password_strength(password)
            validate_password_match(password, confirm_password)

            # If all validations pass, create the user
            user = CustomUser.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile=mobile,
                password=password,
                referral_code=referral_code
            )
           
            otp = generate_otp()
            
             # Store OTP in Redis cache with expiry (e.g., 5 minutes)
            cache_key = f"otp_{email}"
            cache.set(cache_key, otp, timeout=300)  # 300 seconds = 5 minutes
            
            # Send email asynchronously using Celery
            send_welcome_email_task.delay(email, first_name,otp)

            messages.success(request, "Account created successfully! Please check your email.")
            return redirect("enter_otp")

        except ValidationError as e:
            messages.error(request, e.message)
        except IntegrityError:
            messages.error(request, "An account with this email or mobile already exists.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

        context = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "mobile": mobile,
            "referral_code": referral_code,
        }
        return render(request, "signup.html", context)

    return render(request, "signup.html")


def signin(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            if not email or not password:
                raise ValidationError("Both email and password are required.")
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("Please enter a valid email address.")

            user = authenticate(request, email=email, password=password)

            if user is None:
                raise ValidationError("Invalid email or password. Please try again.")

            if not user.is_active:
                raise ValidationError("Your account is inactive. Please contact support.")

            login(request, user)
            # messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect("home")

        except ValidationError as e:
            messages.error(request, e.message)
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

        context = {"email": email}
        return render(request, "signin.html", context)

    return render(request, "signin.html")

def forgot_password(request):
    return render(request,'forgot_password.html')

def enter_otp(request):
    try:
        if request.method == "POST":
            entered_otp = request.POST.get("otp", "").strip()

            #  Check if email is stored in session
            email = request.session.get("email")
            if not email:
                messages.error(request, "Session expired. Please sign up or log in again.")
                return redirect("signup")

            #  Check if OTP is entered
            if not entered_otp:
                messages.warning(request, "Please enter your OTP.")
                return redirect("enter_otp")

            #  Retrieve OTP from Redis cache
            cache_key = f"otp_{email}"
            stored_otp = cache.get(cache_key)

            #  Handle expired or missing OTP
            if stored_otp is None:
                messages.error(request, "OTP has expired or not found. Please request a new one.")
                return redirect("enter_otp")

            #  Compare entered OTP with stored one
            if entered_otp == stored_otp:
                cache.delete(cache_key)  # clear OTP from Redis
                messages.success(request, "OTP verified successfully! Welcome to Vara 🎨")
                
                # Clear session email
                request.session.pop("email", None)
                return redirect("signin")
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect("enter_otp")

        # For GET request, render the OTP page
        return render(request, "enter_otp.html")

    except SuspiciousOperation:
        messages.error(request, "Something went wrong with your session. Please log in again.")
        return redirect("signin")

    except ConnectionError:
        messages.error(request, "Server connection error. Please try again later.")
        return redirect("enter_otp")

    except Exception as e:
        # Log unexpected exceptions if needed
        logger.exception("Error during OTP verification: %s", e)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect("enter_otp")
