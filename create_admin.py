from models import init_db, register_user, get_user

# Make sure the database and tables are initialized
init_db()

# Check if admin user already exists
if not get_user("Nilesh"):
    register_user("Nilesh", "12345", "admin")
    print("✅ Admin user created successfully.")
else:
    print("ℹ️ Admin user already exists.")
