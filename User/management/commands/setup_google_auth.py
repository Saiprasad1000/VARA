from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Setup Google OAuth credentials'

    def add_arguments(self, parser):
        parser.add_argument('client_id', type=str, help='Google OAuth Client ID')
        parser.add_argument('client_secret', type=str, help='Google OAuth Client Secret')

    def handle(self, *args, **options):
        client_id = options['client_id']
        client_secret = options['client_secret']

        # Get or create the default site
        site = Site.objects.get(pk=1)
        
        # Create or update Google social app
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()
            self.stdout.write(self.style.SUCCESS('✅ Google OAuth credentials updated!'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Google OAuth credentials created!'))
        
        # Add site to the social app
        if site not in google_app.sites.all():
            google_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'✅ Added site: {site.domain}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Google Authentication is ready!'))
        self.stdout.write(self.style.WARNING('\nNext steps:'))
        self.stdout.write('1. Make sure your server is running')
        self.stdout.write('2. Add Google Sign-In button to your templates')
        self.stdout.write('3. Test the authentication flow')
