from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_welcome_email_task(email, first_name,otp):


    subject = "🎨 Welcome to Vara – Your Art Journey Begins!"

    # Plain text fallback (for email clients that don't render HTML)
    message = (
        f"Hello {first_name},\n\n"
        f"Welcome to Vara, your destination for discovering and owning beautiful paintings.\n\n"
        f"Your OTP is: {otp}\n\n"
        f"Enter this OTP to verify your account and start exploring.\n\n"
        f"– The Vara Team"
    )

    # HTML version (with styling and highlighted OTP)
    html_message = f"""
    <html>
        <body style="font-family: 'Segoe UI', sans-serif; background-color: #f9f9f9; padding: 30px; color: #333;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 25px;">
                <h2 style="text-align: center; color: #2b2b2b;">🎨 Welcome to <span style="color: #6a1b9a;">Vara</span>!</h2>
                <p style="font-size: 16px;">Hi <strong>{first_name}</strong>,</p>
                <p style="font-size: 16px; line-height: 1.6;">
                    We’re thrilled to have you join our community of art lovers! <br>
                    Your account has been created successfully. To complete your sign-up, please verify your email using the OTP below.
                </p>

                <div style="text-align: center; margin: 40px 0;">
                    <div style="
                        display: inline-block;
                        background: linear-gradient(135deg, #6a1b9a, #9c27b0);
                        color: white;
                        font-size: 32px;
                        font-weight: bold;
                        letter-spacing: 4px;
                        padding: 15px 30px;
                        border-radius: 10px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
                    ">
                        {otp}
                    </div>
                </div>

                <p style="font-size: 15px; color: #555;">
                    Once verified, you can explore and purchase unique paintings that speak to your soul. <br><br>
                    Thank you for choosing <strong>Vara</strong> — where every brushstroke tells a story.
                </p>

                <p style="font-size: 14px; color: #888; text-align: center; margin-top: 40px;">
                    With creativity,<br>
                    <strong>🖌️ The Vara Team</strong><br>
                    <a href="https://www.vara-art.com" style="color: #9c27b0; text-decoration: none;">www.vara-art.com</a>
                </p>
            </div>
        </body>
    </html>
    """

    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        send_mail(
            subject,
            message,              # plain text fallback
            from_email,
            recipient_list,
            fail_silently=False,
            html_message=html_message  # send HTML version
        )
        return f"Email sent successfully to {email} with OTP {otp}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@shared_task
def send_forgot_password_email(email, otp):
    subject = "🔐 Your OTP to Reset Password – VARA"

    message = (
        f"Your OTP to reset your password is: {otp}\n"
        f"Do not share it with anyone.\n\n"
        f"– VARA Team"
    )

    html_message = f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Password Reset OTP</h2>
            <p>Your OTP is:</p>
            <div style="font-size: 30px; font-weight: bold; background: #6a1b9a; color: white; padding: 10px; width: fit-content;">
                {otp}
            </div>
            <p>Please use this OTP to reset your password.</p>
        </body>
    </html>
    """

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            html_message=html_message
        )
    except Exception as e:
        print("Email error:", e)