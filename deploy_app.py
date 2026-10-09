"""Hosting entry point. Fail closed if login secrets are not configured."""
import os
from app import app
from online_security import install_security

install_security(
    app,
    password=os.environ.get('LINKSCOPE_PASSWORD', ''),
    secret_key=os.environ.get('SECRET_KEY', ''),
    secure_cookie=True,
)
