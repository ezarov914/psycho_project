import uuid
from app.db import db_app

def generate_reset_token(email):
    token = str(uuid.uuid4())
    db_app.insert("reset_tokens", {"token": token, "email": email})
    return token

def validate_reset_token(token):
    record = db_app.fetch_one("SELECT * FROM reset_tokens WHERE token = %s", (token,))
    if record:
        return record['email']
    return None
