"""Online entry point: no website password; each visitor supplies their own API key."""
from app import app
from online_security import install_public_security

install_public_security(app)
