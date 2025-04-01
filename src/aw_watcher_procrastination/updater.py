"""Simple auto-update functionality using GitHub releases."""

import sys
import subprocess
from typing import Optional, Tuple
import pkg_resources
import requests

GITHUB_API = "https://api.github.com/repos/gregschwartz/aw-procrastination-monitor/releases/latest"
PACKAGE_NAME = "aw-procrastination-monitor"

def check_for_update() -> Tuple[bool, Optional[str]]:
    """Check if a new version is available on GitHub.
    
    Returns:
        Tuple of (update_available, latest_version)
    """
    try:
        response = requests.get(GITHUB_API)
        response.raise_for_status()
        latest = response.json()["tag_name"].lstrip("v")
        current = pkg_resources.get_distribution(PACKAGE_NAME).version
        return pkg_resources.parse_version(latest) > pkg_resources.parse_version(current), latest
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return False, None

def update_package() -> bool:
    """Update the package using pip.
    
    Returns:
        True if update was successful, False otherwise
    """
    try:
        # Get the package installation directory
        pkg_path = Path(pkg_resources.get_distribution(PACKAGE_NAME).location)
        is_editable = (pkg_path / "setup.py").exists()
        
        if is_editable:
            # If installed in editable/development mode, use git pull
            subprocess.check_call(["git", "pull"], cwd=pkg_path)
        else:
            # Otherwise use pip to upgrade
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "--upgrade", PACKAGE_NAME
            ])
        return True
    except Exception as e:
        print(f"Error during update: {e}")
        return False

def ensure_latest_version() -> None:
    """Check for updates and install if available."""
    needs_update, latest = check_for_update()
    if needs_update and latest:
        print(f"New version {latest} available. Updating...")
        if update_package():
            print("Update successful! Please restart the application.")
            sys.exit(0)
        else:
            print("Update failed. Please update manually.") 