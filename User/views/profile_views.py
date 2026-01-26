from .common_imports import *

@user_required
@never_cache
def edit_profile(request):
    user = request.user
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        new_email = request.POST.get("email", "").strip()
        
        try:
            # Validate basic fields
            validate_name(first_name)
            validate_name(last_name)
            validate_mobile(mobile, exclude_user_id=request.user.id)
            
            # 1. Update Basic details first
            user.first_name = first_name
            user.last_name = last_name
            user.mobile = mobile
            
            # 2. Handle Image Upload
            if 'pro_image' in request.FILES:
                user.pro_image = request.FILES['pro_image']
            
            # 3. Handle Email Change
            if new_email and new_email != user.email:
                # Validate new email format and uniqueness
                if CustomUser.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                    messages.error(request, "This email is already in use by another account.")
                    return redirect('edit_profile')
                
                # Initiate Email Change Verification
                otp = generate_otp()
                
                # Cache keys
                cache_key_otp = f"email_change_otp_{user.id}"
                cache_key_email = f"email_change_new_{user.id}"
                
                # Store in cache (5 mins)
                cache.set(cache_key_otp, otp, timeout=300)
                cache.set(cache_key_email, new_email, timeout=300)
                
                # Send OTP to NEW email
                try:
                    # Using send_update_email_otp task
                    send_update_email_otp.delay(new_email, first_name, otp)
                except Exception as exc:
                    logger.warning("Celery unavailable, sending sync: %s", exc)
                    send_update_email_otp(new_email, first_name, otp)
                
                # Save other changes before redirecting
                user.save()
                
                messages.info(request, "Please verify your new email address.")
                return redirect('verify_email_change')
            
            # No email change, just save
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('edit_profile')

        except ValidationError as e:
            messages.error(request, e.message)
        except Exception as e:
            logger.exception("Error updating profile: %s", e)
            messages.error(request, "An unexpected error occurred.")
            
    return render(request, 'edit_profile.html', {'active_tab': 'edit_profile'})


@user_required
@never_cache
def verify_email_change(request):
    user = request.user
    cache_key_otp = f"email_change_otp_{user.id}"
    cache_key_email = f"email_change_new_{user.id}"
    
    new_email = cache.get(cache_key_email)
    
    if not new_email:
        messages.error(request, "Email change session expired. Please try again.")
        return redirect('edit_profile')
        
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
        stored_otp = cache.get(cache_key_otp)
        
        if stored_otp and entered_otp == str(stored_otp):
            # Verify success
            try:
                user.email = new_email
                user.save()
                
                # Clear cache
                cache.delete(cache_key_otp)
                cache.delete(cache_key_email)
                
                messages.success(request, f"Email updated successfully to {new_email}!")
                return redirect('edit_profile')
            except IntegrityError:
                messages.error(request, "This email is already in use.")
                return redirect('edit_profile')
        else:
            messages.error(request, "Invalid or expired OTP.")
    
    return render(request, 'verify_email_change.html', {'new_email': new_email})
