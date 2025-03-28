from auth import register_user, login_user

# Test User Registration
if register_user("Shivam", "Kumar", "shivam@example.com", "mypassword"):
    print("✅ User Registered Successfully")
else:
    print("❌ Email Already Exists")

# Test Login
if login_user("shivam@example.com", "mypassword"):
    print("✅ Login Successful")
else:
    print("❌ Login Failed")
