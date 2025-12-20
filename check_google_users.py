"""
Quick script to check if Google authentication is working
Run with: python check_google_users.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vara.settings')
django.setup()

from User.models import CustomUser
from allauth.socialaccount.models import SocialAccount

print("=" * 60)
print("🔍 GOOGLE AUTHENTICATION STATUS CHECK")
print("=" * 60)

# Check total users
total_users = CustomUser.objects.count()
print(f"\n📊 Total Users: {total_users}")

# Check Google-authenticated users
google_accounts = SocialAccount.objects.filter(provider='google')
print(f"🔐 Google Authenticated Users: {google_accounts.count()}")

if google_accounts.exists():
    print("\n✅ Google Authentication is WORKING!\n")
    print("Google Users:")
    for account in google_accounts:
        user = account.user
        print(f"  • {user.email} (ID: {user.id})")
        print(f"    - Google UID: {account.uid}")
        print(f"    - Joined: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
else:
    print("\n⚠️  No Google users found yet.")
    print("   Try logging in with Google to test!")

print("\n" + "=" * 60)
