# Auth Views – Explanation

This document explains each view function in `Vara/User/views/auth_views.py`.

---

## 1. `index(request)`

**Purpose:** Show the landing page with some products.

**What it does:**
- Fetches the latest products that are *not deleted*:
  - `Product.objects.filter(is_deleted=False).order_by('-created_at')[:8]`
- Puts them in a context dictionary as `best_sellers`.
- Renders the `index.html` template with that context.

Result: The homepage shows a small selection of recent products.

---

## 2. `signup(request)`

**Purpose:** Handle user registration and send an OTP to email for verification.

**Main steps (POST request):**
1. **Read form data** from `request.POST`:
   - `first_name`, `last_name`, `email`, `mobile`, `password`, `confirm_password`, `referral_code`.
2. **Store email in session**:
   - `request.session["email"] = email`
   - This is used later for OTP verification.
3. **Validate the fields** using custom validators:
   - `validate_name(first_name)`
   - `validate_name(last_name)`
   - `validate_email_unique(email)` – make sure email is not already used.
   - `validate_mobile(mobile)`
   - `validate_password_strength(password)`
   - `validate_password_match(password, confirm_password)`
4. **Create the user** if all validations pass:
   - `CustomUser.objects.create_user(...)`
   - Saves first name, last name, email, mobile, password, and referral code.
5. **Generate an OTP**:
   - `otp = generate_otp()`
6. **Store the OTP in cache (Redis) with a 5‑minute expiry**:
   - Key: `otp_{email}`
   - `cache.set(cache_key, otp, timeout=300)`
7. **Send a welcome/OTP email asynchronously using Celery**:
   - `send_welcome_email_task.delay(email, first_name, otp)`
8. **Show a success message and redirect** to the OTP page:
   - `messages.success(...)
   - `return redirect("enter_otp")`

**Error handling:**
- `ValidationError` → show user-friendly validation message.
- `IntegrityError` → email or mobile already exists.
- Any other exception → generic error message.

**GET request:**
- Just renders `signup.html` (empty form).

---

## 3. `signin(request)`

**Purpose:** Log the user in with email and password.

**Main steps (POST request):**
1. Read `email` and `password` from the form.
2. Validate:
   - Both fields must be present.
   - `validate_email(email)` to ensure format is correct.
3. Authenticate:
   - `user = authenticate(request, email=email, password=password)`
   - If `user` is `None`, credentials are invalid.
4. Check if user is active:
   - If `not user.is_active`, raise an error.
5. Log the user in:
   - `login(request, user)`
6. Redirect:
   - If `user.is_superuser` → redirect to `admin_home`.
   - Else → redirect to `home`.

**Error handling:**
- `ValidationError` → show the specific message.
- Generic `Exception` → show unexpected error message.

**GET request:**
- Renders `signin.html` (login form).

---

## 4. `forgot_password(request)`

**Purpose:** Start the password reset process by sending an OTP to the user’s email.

**Main steps (POST request):**
1. Read `email` from the form.
2. Check if a user with that email exists:
   - If not → error message and redirect back to `forgot_password`.
3. Log email to the logger (for debugging/info).
4. Generate an OTP:
   - `otp = generate_otp()`
5. Store OTP in cache with key `otp_reset_{email}` for 5 minutes.
6. Store email in session: `request.session["email"] = email`.
7. Send OTP email using Celery task:
   - `send_forgot_password_email.delay(email, otp)`
8. Show success message and redirect to `enter_otp_fp`.

**GET request:**
- Renders `forgot_password.html`.

---

## 5. `enter_otp_fp(request)` (OTP for forgot password)

**Purpose:** Verify the OTP entered by the user during the password reset flow.

**Main steps (POST request):**
1. Get `entered_otp` from the form.
2. Get `email` from the session.
   - If missing → session expired → redirect to `forgot_password`.
3. If no OTP was entered → warning and redirect to `enter_otp_fp`.
4. Read stored OTP from cache using key `otp_reset_{email}`.
   - If `stored_otp` is `None` → expired → redirect with error.
5. Compare:
   - If `entered_otp == str(stored_otp)`:
     - Delete the OTP from cache.
     - Show success message.
     - Redirect to `reset_password`.
   - Else → show "Invalid OTP" and redirect back.

**GET request:**
- Renders `enter_otp_fp.html`.

**Error handling:**
- Catches any `Exception`, logs it, and shows a generic error.

---

## 6. `reset_password(request)`

**Purpose:** Let the user set a new password after OTP verification.

**Main steps:**
1. Ensure `email` is present in the session.
   - If not → session expired → redirect to `forgot_password`.
2. On POST:
   - Read `new_password` and `confirm_password` from the form.
   - Validate:
     - `validate_password_strength(new_password)`
     - `validate_password_match(new_password, confirm_password)`
   - If validation fails → show error and re-render `reset_password.html`.
3. If validation passes:
   - Get the user by email: `CustomUser.objects.get(email=email)`.
   - Set password using `user.set_password(new_password)` and `user.save()`.
   - Remove `email` from session.
   - Show success message and redirect to `signin`.

**Error handling:**
- If user does not exist → show "User not found".
- Any other exception → log and show generic error.

---

## 7. `enter_otp(request)` (OTP after signup)

**Purpose:** Verify the OTP sent after signup to confirm the user’s email.

**Main steps (POST request):**
1. Get `entered_otp` from the form.
2. Read `email` from session.
   - If missing → session expired → redirect to `signup`.
3. If OTP is empty → warning and redirect to `enter_otp`.
4. Read stored OTP from cache using key `otp_{email}`.
   - If `stored_otp` is `None` → expired or not found → redirect with error.
5. Compare:
   - If `entered_otp == str(stored_otp)`:
     - Delete OTP from cache.
     - Show success message ("Welcome to Vara 🎨").
     - Redirect to `signin`.
   - Else → show invalid OTP message and redirect back.

**GET request:**
- Renders `enter_otp.html`.

**Error handling:**
- `SuspiciousOperation` → session error, redirect to `signin`.
- `ConnectionError` → server connection issue, redirect to `enter_otp`.
- Any other exception → log and show generic error.

---

## 8. `resend_otp(request)`

**Purpose:** Resend OTP email after signup (supports normal and AJAX requests).

**Key idea:** Behavior changes based on whether the request is AJAX.

**Main steps:**
1. Detect AJAX:
   - `is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'`.
2. Get `email` from session.
   - If missing → session expired:
     - For AJAX → return JSON error.
     - For normal → show message and redirect to `signup`.
3. Optionally get the user’s first name for a nicer email greeting.
4. Generate new OTP and store it in cache with key `otp_{email}` for 5 minutes.
5. Send OTP email again with `send_welcome_email_task.delay(email, first_name, otp)`.
6. Respond:
   - For AJAX → return JSON with success message.
   - For normal → use Django messages and redirect to `enter_otp`.

**Error handling:**
- `ConnectionError` → appropriate JSON or message based on AJAX/non‑AJAX.
- Other exceptions → also handled separately for AJAX and normal requests with JSON/messages.

---

## 9. `logout_view(request)`

**Purpose:** Log the user out and clear their session.

**Main steps:**
1. If the user is authenticated:
   - Call `logout(request)` to clear the session.
   - Show success message.
2. Else:
   - Show info message that user is not logged in.
3. Redirect to `index`.

**Error handling:**
- On any exception → log it and redirect to `home` with an error message.

---

## 10. `profile(request)`

**Purpose:** Render the user profile page.

**What it does:**
- Simply returns `render(request, 'profile.html')`.
- Actual profile content/layout is in the template.

---

This document is meant to give you a high-level but clear explanation of each authentication-related view so you can understand and modify your auth flow more easily.
