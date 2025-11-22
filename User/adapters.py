from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):
    def get_signup_form_initial_data(self, request):
        """Ensure username is not requested"""
        data = super().get_signup_form_initial_data(request)
        data.pop("username", None)
        return data

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Get name fields safely
        first_name = data.get("first_name") or data.get("given_name") or ""
        last_name = data.get("last_name") or data.get("family_name") or ""

        # Handle missing names
        if not first_name and not last_name:
            full_name = data.get("name")
            if full_name:
                parts = full_name.split(" ", 1)
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = parts[1]
                else:
                    last_name = "User"

        # Default fallback values if still empty
        user.first_name = first_name or "first name"
        user.last_name = last_name or "last name"
        user.email = data.get("email", "")

        return user

    def save_user(self, request, sociallogin, form=None):
        """Save user and create wallet"""
        user = super().save_user(request, sociallogin, form)
        # You can do post-save logic here (e.g., wallet creation)
        return user
