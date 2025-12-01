
"""
Context processor providing site branding variables to all templates.

The values are loaded from a YAML/JSON configuration via
``patriot.config_loader.get_config``.  The instance is selected by the
``INSTANCE_NAME`` environment variable (default is ``patriot``).
"""

import os
from django.conf import settings
from patriot.config_loader import get_config


def site_constants(request):
    """
    Return a dictionary of site constants and branding values.

    The returned dictionary includes the following keys:
    - ``SITE``: a dict containing NAME, LONG_NAME, LOGO_LIGHT, LOGO_DARK,
      THEME_CSS, PRIMARY_COLOR and SECONDARY_COLOR.  These values are
      retrieved from the configuration file for the current instance.
    - ``SITE_NAME``: shorthand alias for the site name.
    - ``SITE_LONG_NAME``: shorthand alias for the site's long name.
    - ``THEME``: the Bootstrap theme ("light" or "dark").

    If a key is missing in the configuration, reasonable defaults are used
    (e.g. ``FRDM`` for the site name).
    """
    # Determine current instance (fall back to 'patriot')
    instance_name = os.getenv("INSTANCE_NAME", "patriot").strip().lower()
    config = get_config(instance_name)

    # Provide sensible defaults if values are missing
    site_name = config.get("SITE_NAME", "FRDM")
    site_long = config.get("SITE_LONG_NAME", "Freedom Business Directory")

    site = {
        "NAME": site_name,
        "LONG_NAME": site_long,
        "LOGO_LIGHT": config.get("LOGO_LIGHT", "img/logos/FRDM_master_logo.svg"),
        "LOGO_DARK": config.get("LOGO_DARK", "img/logos/FRDM_master_logo_white.svg"),
        "THEME_CSS": config.get("THEME_CSS", "css/styles.css"),
        "ADMIN_CSS": config.get("ADMIN_CSS", "css/custom_admin.css"),
        "PRIMARY_COLOR": config.get("PRIMARY_COLOR"),
        "SECONDARY_COLOR": config.get("SECONDARY_COLOR"),
    }
    return {
        "SITE": site,
        "SITE_NAME": site_name,
        "SITE_LONG_NAME": site_long,
        "THEME": config.get("THEME", "light"),
    }
