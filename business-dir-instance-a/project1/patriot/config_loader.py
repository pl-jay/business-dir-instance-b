"""
Utility functions for loading site configuration for different instances.

This module reads a YAML configuration file containing per‑instance values for
site branding (names, logos, theme CSS, etc.).  The instance name can be
selected via the ``INSTANCE_NAME`` environment variable (default: ``patriot``).

Example ``config.yaml`` file::

    patriot:
      SITE_NAME: "Patriot Directory"
      SITE_LONG_NAME: "Freedom Business Directory"
      LOGO_LIGHT: "img/logos/FRDM_master_logo.svg"
      LOGO_DARK: "img/logos/FRDM_master_logo_white.svg"
      THEME_CSS: "css/styles.css"
      PRIMARY_COLOR: "#e95454"
      SECONDARY_COLOR: "#3d5175"
      THEME: "light"

    masonic:
      SITE_NAME: "Masonic Directory"
      ...

The configuration file must reside at the project root (next to ``manage.py``),
or you can specify a different location via the ``SITE_CONFIG_PATH``
environment variable.

This module exposes a single function ``get_config`` which returns the
dictionary of values for the selected instance.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Dict, Any


def _resolve_config_path() -> Path:
    """Return the path to the configuration file.

    The environment variable ``SITE_CONFIG_PATH`` can be used to override
    the default location (``BASE_DIR / 'config.yaml'``).  ``BASE_DIR`` is
    assumed to be two directories up from this module (i.e., the project root).
    """
    env_path = os.getenv("SITE_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    # Default: project root/config.yaml
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "config.yaml"


def get_config(instance_name: str | None = None, config_path: Path | None = None) -> Dict[str, Any]:
    """
    Load and return the configuration dictionary for ``instance_name``.

    :param instance_name: The key of the instance in the YAML file.  If not
        provided, the value is read from the ``INSTANCE_NAME`` environment
        variable (default: ``patriot``).
    :param config_path: Optional explicit path to the config file.  If not
        provided, ``SITE_CONFIG_PATH`` or the default location is used.
    :returns: A dictionary of configuration values for the instance.  If the
        instance is not found, an empty dict is returned.
    """
    name = (instance_name or os.getenv("INSTANCE_NAME", "patriot")).strip().lower()
    path = config_path or _resolve_config_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        # If the config file is missing, return empty config
        return {}
    return data.get(name, {}) or {}