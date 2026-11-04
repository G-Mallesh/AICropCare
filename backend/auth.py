
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from backend.database import get_db_connection
from backend.extensions import limiter


# =====================================
# AUTHENTICATION BLUEPRINT
# =====================================

auth = Blueprint("auth", __name__)


# =====================================
# ADMIN ACCESS PROTECTION
# =====================================

def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))

        return func(*args, **kwargs)

    return wrapper


# =====================================
# FARMER REGISTRATION
# =====================================

@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not all([name, email, phone, password]):
            flash("Please fill in all fields.", "warning")
            return render_template("register.html")

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "warning"
            )
            return render_template("register.html")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()

            if connection is None:
                raise RuntimeError("Database connection failed.")

            cursor = connection.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("Email already registered.", "warning")
                return render_template("register.html")

            hashed_password = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users
                (name, email, phone, password, role)
                VALUES (%s, %s, %s, %s, 'farmer')
                """,
                (name, email, phone, hashed_password)
            )

            connection.commit()

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect(url_for("auth.login"))

        except Exception as error:

            if connection is not None:
                connection.rollback()

            print("Registration error:", error)

            flash(
                "Registration failed. Please try again.",
                "danger"
            )

        finally:

            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    return render_template("register.html")


# =====================================
# USER LOGIN - ADMIN AND FARMER
# =====================================

@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        if not email or not password:
            flash(
                "Please enter email and password.",
                "warning"
            )
            return render_template("login.html")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()

            if connection is None:
                raise RuntimeError("Database connection failed.")

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, name, email, password, role
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user or not check_password_hash(
                user["password"],
                password
            ):
                flash(
                    "Invalid email or password.",
                    "danger"
                )
                return render_template("login.html")

            if user["role"] not in ("admin", "farmer"):
                flash(
                    "Unauthorized account role.",
                    "danger"
                )
                return render_template("login.html")

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = user["role"]

            flash("Login successful!", "success")

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        except Exception as error:

            print("Login error:", error)

            flash(
                "Unable to login. Please try again.",
                "danger"
            )

        finally:

            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    return render_template("login.html")


# =====================================
# USER LOGOUT
# =====================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("home"))
