# app/create_first_admin.py

from app.database import SessionLocal
from app.models.user import User
from app.security.encryption import hash_password

db = SessionLocal()

email = "mehu@example.com"
password = "password123"

# Check if user exists
existing = db.query(User).filter(User.email == email).first()
if existing:
    print("User already exists")
    exit()

user = User(
    email=email,
    hashed_password=hash_password(password),
    role="admin",
    is_active=True
)

db.add(user)
db.commit()
db.refresh(user)
print(f"Admin user created: {user.email}")
