from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        # Only allow auto-linking/creation if email is verified by Keycloak
        return bool(claims.get('email')) and bool(claims.get('email_verified'))

    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if not email:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(email__iexact=email)

    def create_user(self, claims):
        user = super().create_user(claims)
        user.email = claims.get('email', '')
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.set_unusable_password()  # important: no local password for KC users
        user.save()
        return user
