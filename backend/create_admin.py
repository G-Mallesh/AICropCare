from werkzeug.security import generate_password_hash

password = input("Enter admin password: ")

if len(password) < 12:
    print("Use at least 12 characters for the admin password.")
else:
    print("\nCopy this hash into your MySQL INSERT statement:\n")
    print(generate_password_hash(password))