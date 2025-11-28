from .common_imports import *

def index(request):
    # Fetch products for the landing page
    products = Product.objects.filter(is_deleted=False).order_by('-created_at')[:8]
    
    context = {
        'best_sellers': products
    }
    return render(request, 'index.html', context)


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
            if user.is_superuser:
                return redirect('admin_home')
            return redirect("home")

        except ValidationError as e:
            messages.error(request, e.message)
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

        context = {"email": email}
        return render(request, "signin.html", context)

    return render(request, "signin.html")

def forgot_password(request):  
    if request.method == "POST":
        email = request.POST.get("email")

        if not CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email not found')
            return redirect("forgot_password")

        logger.info(f"user entered email: {email}")

        otp = generate_otp()

        cache_key = f"otp_reset_{email}"
        cache.set(cache_key, otp, timeout=300)  # 5 minutes

        # Save email in session
        request.session["email"] = email

        # FIXED: correct order of arguments
        send_forgot_password_email.delay(email, otp)

        messages.success(request, 'OTP sent! Please check your email.')
        return redirect("enter_otp_fp")

    return render(request, 'forgot_password.html')

    
    
def enter_otp_fp(request):
    try:
        if request.method == "POST":
            entered_otp = request.POST.get("otp", "").strip()

            email = request.session.get("email")

            if not email:
                messages.error(request, "Session expired.")
                return redirect("forgot_password")

            if not entered_otp:
                messages.warning(request, "Please enter your OTP.")
                return redirect("enter_otp_fp")

            cache_key = f"otp_reset_{email}"
            stored_otp = cache.get(cache_key)

            if stored_otp is None:
                messages.error(request, "OTP expired. Please resend.")
                return redirect("enter_otp_fp")

            if entered_otp == str(stored_otp):
                cache.delete(cache_key)
                messages.success(request, "OTP verified successfully!")

                return redirect("reset_password")
            else:
                messages.error(request, "Invalid OTP.")
                return redirect("enter_otp_fp")

        return render(request, "enter_otp_fp.html")

    except Exception as e:
        logger.exception("OTP verification error: %s", e)
        messages.error(request, "Unexpected error.")
        return redirect("enter_otp_fp")




def reset_password(request):
    """Reset password after OTP verification"""
    try:
        # Check if email is in session (from OTP verification)
        email = request.session.get("email")
        if not email:
            messages.error(request, "Session expired. Please start the password reset process again.")
            return redirect("forgot_password")

        if request.method == "POST":
            new_password = request.POST.get("new_password", "").strip()
            confirm_password = request.POST.get("confirm_password", "").strip()

            # Validate passwords
            try:
                validate_password_strength(new_password)
                validate_password_match(new_password, confirm_password)
            except ValidationError as e:
                messages.error(request, e.message)
                return render(request, "reset_password.html")

            # Update user password
            try:
                user = CustomUser.objects.get(email=email)
                user.set_password(new_password)
                user.save()

                # Clear session email
                request.session.pop("email", None)

                messages.success(request, "Password reset successfully! Please log in with your new password.")
                return redirect("signin")

            except CustomUser.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect("forgot_password")

        return render(request, "reset_password.html")

    except Exception as e:
        logger.exception(f"Error in reset_password: {e}")
        messages.error(request, "An unexpected error occurred.")
        return redirect("forgot_password")
    
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

            #  Compare entered OTP with stored one (ensure both are strings)
            if entered_otp == str(stored_otp):
                cache.delete(cache_key)  # clear OTP from Redis
                messages.success(request, "OTP verified successfully! Welcome to Vara 🎨")
                
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


def resend_otp(request):
    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        email = request.session.get("email")

        if not email:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Session expired. Please sign up again.'
                }, status=400)
            else:
                messages.error(request, "Session expired. Please sign up again.")
                return redirect("signup")

        # Get user first name (optional, for email greeting)
        user = CustomUser.objects.filter(email=email).first()
        first_name = user.first_name if user else "User"

        # Generate new OTP
        otp = generate_otp()

        # Update Redis cache with new OTP (valid for 5 mins)
        cache_key = f"otp_{email}"
        cache.set(cache_key, otp, timeout=300)

        # Send new OTP email via Celery
        send_welcome_email_task.delay(email, first_name, otp)

        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': 'A new OTP has been sent to your email.'
            })
        else:
            messages.success(request, "A new OTP has been sent to your email.")
            return redirect("enter_otp")

    except ConnectionError:
        logger.exception("Connection error during OTP resend")
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'Server connection error. Please try again later.'
            }, status=500)
        else:
            messages.error(request, "Server connection error. Please try again later.")
            return redirect("enter_otp")

    except Exception as e:
        logger.exception("Error during OTP resend: %s", e)
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred while resending OTP.'
            }, status=500)
        else:
            messages.error(request, "An unexpected error occurred while resending OTP.")
            return redirect("enter_otp")


def logout_view(request):
    try:
        if request.user.is_authenticated:
            logout(request)  #Clears the session and logs out the user
            messages.success(request, "You’ve been logged out successfully.")
        else:
            messages.info(request, "You’re not logged in.")
        return redirect("index")  # Redirect to login page after logout
    except Exception as e:
        logger.info(f"Logout error: {str(e)}")
        messages.error(request, "An error occurred while logging out.")
        return redirect("home")
    
def profile(request):
    return render(request,'profile.html')
