import sys
from app.database import SessionLocal
from app.main import seed_demo_users
from app.models import User
from app.auth import verify_password
import bcrypt

try:
    db = SessionLocal()
    seed_demo_users(db)
    user = db.query(User).filter_by(username="admin_demo").first()
    print(f"User: {user.username}, Hash: {user.password_hash}")
    print("Verify:", verify_password("Admin@123", user.password_hash))
except Exception as e:
    print(f"Error: {e}")
