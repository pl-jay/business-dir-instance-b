from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from .forms import SignupForm
from .keycloak_bridge import create_user, set_temporary_password, set_required_actions
import secrets, string

User = get_user_model()

def _gen_temp_password(n=12):
    alphabet = string.ascii_letters + string.digits
    # Simple: add at least one symbol to satisfy common KC password policies (adjust to yours)
    base = ''.join(secrets.choice(alphabet) for _ in range(n-2))
    return base + '!'  # ensure a symbol

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("directory:list")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email') or form.cleaned_data['username']
            first = form.cleaned_data.get('first_name', '')
            last  = form.cleaned_data.get('last_name', '')

            # 1) Local profile row (no password stored locally)
            user, _ = User.objects.get_or_create(username=email, defaults={'email': email})
            user.email = email
            user.first_name = first
            user.last_name = last
            user.set_unusable_password()
            user.save()

            # 2) Provision Keycloak user
            kc_id = create_user(email=email, first_name=first, last_name=last)

            # 3) Set temp password and force change on first login
            temp_pw = form.cleaned_data.get('password2', '')#_gen_temp_password()
            set_temporary_password(kc_id, temp_pw)             # temporary=True
            set_required_actions(kc_id, ('UPDATE_PASSWORD',))   # prompt to change after login

            # 4) Tell the user the temp password once (DEV: show; PROD: deliver via secure channel)
            messages.success(request, f"Account created. Temporary password: {temp_pw}. You’ll be asked to change it after sign in.")

            # 5) Send them to KC login
            return redirect('oidc_authentication_init')
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})



# from django.contrib import messages
# from django.shortcuts import redirect, render
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from django.conf import settings
# from .forms import SignupForm
# from .keycloak_bridge import create_user, send_actions_email

# User = get_user_model()

# def signup_view(request):
#     if request.user.is_authenticated:
#         return redirect("directory:list")  # or wherever

#     if request.method == "POST":
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data.get('email') or form.cleaned_data['username']
#             first = getattr(form.cleaned_data, 'first_name', '') if hasattr(form.cleaned_data, 'first_name') else ''
#             last  = getattr(form.cleaned_data, 'last_name', '') if hasattr(form.cleaned_data, 'last_name') else ''

#             # 1) Create local profile row (no local password – Keycloak is source of truth)
#             user, created = User.objects.get_or_create(username=email, defaults={'email': email})
#             user.email = email
#             user.first_name = first
#             user.last_name = last
#             user.set_unusable_password()
#             user.save()

#             # 2) Provision in Keycloak + send verify/set-password email
#             kc_id = create_user(email=email, first_name=first, last_name=last)
#             print( "Created Keycloak user ID:", kc_id )
#             post_redirect = request.build_absolute_uri(reverse("directory:list"))  # safer target
#             print( "Post redirect URI:", post_redirect )
#             send_actions_email(
#                 kc_id,
#                 actions=('VERIFY_EMAIL','UPDATE_PASSWORD'),
#                 client_id=settings.OIDC_RP_CLIENT_ID,   # must be your BROWSER client, i.e. 'nra-bs-dir'
                
#             )

#             messages.success(request, "Account created. Please check your email to verify and set a password.")
#             # 3) Send them to Keycloak login flow now
#             return redirect('oidc_authentication_init')
#     else:
#         form = SignupForm()

#     return render(request, "registration/signup.html", {"form": form})


from django.shortcuts import render

def terms_views(request):
    return render(request, "legal/terms.html")

def privacy_views(request):
    return render(request, "legal/privacy.html")