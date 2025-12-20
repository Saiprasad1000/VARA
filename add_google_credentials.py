"""
Quick script to add Google OAuth credentials
Run this with: python add_google_credentials.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vara.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site



GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def setup_google_auth():
    print("🔧 Setting up Google OAuth...")
    
    # Get or update the default site
    site = Site.objects.get(pk=1)
    site.domain = '127.0.0.1:8000'
    site.name = 'VARA'
    site.save()
    print(f"✅ Site configured: {site.domain}")
    
    # Create or update Google social app
    google_app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google',
            'client_id': CLIENT_ID,
            'secret': CLIENT_SECRET,
        }
    )
    
    # Add site to the social app
    google_app.sites.clear()
    google_app.sites.add(site)
    
    if created:
        print("✅ Google OAuth credentials created!")
    else:
        print("✅ Google OAuth credentials updated!")
    
    print("\n🎉 Setup complete!")
    print(f"   Client ID: {CLIENT_ID[:20]}...")
    print(f"   Site: {site.domain}")
    print("\n📝 Next steps:")
    print("   1. Make sure your server is running")
    print("   2. Go to your signin page")
    print("   3. Click 'Continue with Google'")
    print("   4. Test the authentication!")

if __name__ == '__main__':
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE" or CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
        print("❌ ERROR: Please replace CLIENT_ID and CLIENT_SECRET with your actual credentials!")
        print("\nGet them from: https://console.cloud.google.com/")
        print("   → APIs & Services → Credentials → OAuth 2.0 Client IDs")
    else:
        setup_google_auth()
