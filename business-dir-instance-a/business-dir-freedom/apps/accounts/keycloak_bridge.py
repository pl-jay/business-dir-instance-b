# apps/accounts/keycloak_bridge.py
import os
import requests
import urllib3
import logging
log = logging.getLogger(__name__)

# <-- TEMP DEV ONLY: disable InsecureRequestWarning so logs are not noisy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE  = os.getenv('KEYCLOAK_BASE').rstrip('/')
REALM = os.getenv('KEYCLOAK_REALM')
CID   = os.getenv('KC_BRIDGE_CLIENT_ID')
CSEC  = os.getenv('KC_BRIDGE_CLIENT_SECRET')

# helper: centralize verify behavior via env var
VERIFY_KC_TLS = os.getenv('KC_VERIFY_TLS', 'false').lower() in ('true', '1', 'yes')

def _token():
    url = f"{BASE}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': CID,
        'client_secret': CSEC,
    }
    # pass verify=VERIFY_KC_TLS (False for dev)
    r = requests.post(url, data=data, timeout=10, verify=VERIFY_KC_TLS)
    r.raise_for_status()
    return r.json()['access_token']

def _admin():
    tok = _token()
    print("-----------")

    print("KC Admin Token:", tok)  # --- IGNORE ---
    print("-----------")

    return {
        'base': f"{BASE}/admin/realms/{REALM}",
        'headers': {'Authorization': f"Bearer {tok}", 'Content-Type': 'application/json'},
        'verify': VERIFY_KC_TLS
    }

def find_user_by_email(email):
    a = _admin()
    r = requests.get(f"{a['base']}/users", headers=a['headers'],
                     params={'email': email}, timeout=10, verify=a['verify'])
    r.raise_for_status()
    arr = r.json()
    return arr[0] if arr else None

def create_user(email, first_name='', last_name=''):
    existing = find_user_by_email(email)
    if existing:
        return existing['id']

    a = _admin()
    print("-----------")

    print("Creating KC user:", email, first_name, last_name)  # --- IGNORE ---
    print("Admin details:", a)  # --- IGNORE ---
    print("-----------")
    payload = {
        "username": email,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": False,
    }
    r = requests.post(f"{a['base']}/users", headers=a['headers'],
                      json=payload, timeout=10, verify=a['verify'])
    if r.status_code == 201:
        user_id = r.headers['Location'].rstrip('/').split('/')[-1]
        return user_id
    elif r.status_code == 409:
        u = find_user_by_email(email)
        return u['id'] if u else None
    else:
        r.raise_for_status()

def send_actions_email(user_id, actions=('VERIFY_EMAIL','UPDATE_PASSWORD'), client_id=None, redirect_uri=None):
    try:
        a = _admin()
        params = {}
        if client_id:
            params['client_id'] = client_id
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        r = requests.put(
            f"{a['base']}/users/{user_id}/execute-actions-email",
            headers=a['headers'],
            params=params,
            json=list(actions),
            timeout=10,
            verify=a['verify']
        )
        r.raise_for_status()
    except Exception as e:
        body = e.response.text if e.response is not None else ''
        log.error("KC execute-actions-email failed: %s %s", e, body)
        print("-----------")
        print("Sent actions email to KC user ID:", user_id)  # --- IGNORE ---
        print("Actions:", body)  # --- IGNORE ---
        print("-----------")

        raise
def set_required_actions(user_id, actions=('UPDATE_PASSWORD',)):
    """
    Add required actions (e.g., UPDATE_PASSWORD) so KC prompts on next login.
    """
    a = _admin()
    r = requests.put(
        f"{a['base']}/users/{user_id}",
        headers=a['headers'],
        json={"requiredActions": list(actions)},
        timeout=10,
        verify=a.get('verify', True)
    )
    r.raise_for_status()

def set_temporary_password(user_id, temp_password):
    a = _admin()
    r = requests.put(
        f"{a['base']}/users/{user_id}/reset-password",
        headers=a['headers'],
        json={"type": "password", "value": temp_password, "temporary": True},
        timeout=10,
        verify=a.get('verify', True)
    )
    r.raise_for_status()
