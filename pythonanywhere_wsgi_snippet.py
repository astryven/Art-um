# Paste this ENTIRE file's contents into your PythonAnywhere WSGI configuration file
# (Web tab -> "WSGI configuration file"), replacing what's there.
# Change YOURUSERNAME to your PythonAnywhere username.
import os
import sys

project_home = "/home/YOURUSERNAME/arteum"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ["ARTEUM_ENV"] = "production"

from app import app as application  # noqa: E402
