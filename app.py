
import os
import uuid

import requests
from PIL import Image

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect, CSRFError

from backend.auth import auth, admin_required
from backend.database import get_db_connection
from backend.extensions import limiter

from backend.detection import predict_disease
from backend.recommendations import get_disease_recommendation
from backend.chatbot import get_farming_answer
from backend.weather import get_weather, get_farming_advice
from backend.analytics import get_farmer_analytics


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

app.config.from_object("config.Config")

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY") or app.config.get("SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.getenv("FLASK_ENV") == "production"
    ),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024
)

if not app.config.get("SECRET_KEY"):
    raise RuntimeError(
        "SECRET_KEY is missing. Configure it before starting Flask."
    )

# Register authentication blueprint once.
app.register_blueprint(auth)

# Initialize CSRF protection once.
csrf = CSRFProtect(app)

# Initialize rate limiter once.
limiter.init_app(app)


# --------------------------------------------------
# IMAGE UPLOAD CONFIGURATION
# --------------------------------------------------

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

UPLOAD_FOLDER = os.path.join(
    app.static_folder,
    "uploads"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# CROP DISEASE DETECTION
# --------------------------------------------------

@app.route("/detect", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def detect():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("detect.html")

    if "crop_image" not in request.files:
        flash("Please select a crop image.", "warning")
        return redirect(url_for("detect"))

    file = request.files["crop_image"]
    crop_name = request.form.get("crop_name", "").strip()

    if not crop_name:
        flash("Please select a crop type.", "warning")
        return redirect(url_for("detect"))

    if not file.filename:
        flash("Please select an image.", "warning")
        return redirect(url_for("detect"))

    if not allowed_file(file.filename):
        flash(
            "Only JPG, JPEG and PNG images are allowed.",
            "danger"
        )
        return redirect(url_for("detect"))

    filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4()}_{filename}"

    image_path = os.path.join(UPLOAD_FOLDER, filename)

    connection = None
    cursor = None

    try:
        file.save(image_path)

        if os.path.getsize(image_path) > 5 * 1024 * 1024:
            flash("Image size must be below 5 MB.", "danger")
            return redirect(url_for("detect"))

        # Verify that the uploaded file is a valid image.
        with Image.open(image_path) as image:
            image.verify()

        # Predict disease.
        disease_name, confidence = predict_disease(image_path)

        recommendation = get_disease_recommendation(disease_name)

        # Save prediction to database.
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO detections
            (
                user_id,
                crop_name,
                image_path,
                disease_name,
                confidence
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                crop_name,
                "uploads/" + filename,
                disease_name,
                confidence
            )
        )

        connection.commit()

        return render_template(
            "detect.html",
            result=disease_name,
            confidence=confidence,
            image_path="uploads/" + filename,
            recommendation=recommendation
        )

    except Exception as error:

        if connection is not None:
            connection.rollback()

        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass

        app.logger.exception("Detection error: %s", error)

        flash(
            "Detection unavailable. Check the model, database, "
            "and recommendation configuration.",
            "danger"
        )

        return redirect(url_for("detect"))

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# --------------------------------------------------
# FARMER DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None

    stats = {
        "total": 0,
        "healthy": 0,
        "diseased": 0
    }

    detections = []

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM detections
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        stats["total"] = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS diseased
            FROM detections
            WHERE user_id = %s
            AND LOWER(disease_name) NOT LIKE '%healthy%'
            """,
            (session["user_id"],)
        )

        stats["diseased"] = cursor.fetchone()["diseased"]
        stats["healthy"] = stats["total"] - stats["diseased"]

        cursor.execute(
            """
            SELECT *
            FROM detections
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (session["user_id"],)
        )

        detections = cursor.fetchall()

    except Exception as error:
        app.logger.exception("Dashboard error: %s", error)
        flash("Unable to load dashboard data.", "danger")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        detections=detections
    )


# --------------------------------------------------
# DETECTION HISTORY
# --------------------------------------------------

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = None
    cursor = None
    detections = []

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM detections
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )

        detections = cursor.fetchall()

    except Exception as error:
        app.logger.exception("History error: %s", error)
        flash("Unable to load detection history.", "danger")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    return render_template(
        "history.html",
        detections=detections
    )


# --------------------------------------------------
# ADMIN DASHBOARD
# admin_required is imported from backend.auth
# --------------------------------------------------

@app.route("/admin")
@admin_required
def admin():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM users WHERE role='farmer'"
        )
        total_farmers = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM crops"
        )
        total_crops = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM diseases"
        )
        total_diseases = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM detections"
        )
        total_detections = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT
                d.id,
                d.crop_name,
                d.disease_name,
                d.confidence,
                d.created_at,
                u.name AS farmer_name
            FROM detections d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.created_at DESC
            LIMIT 10
            """
        )

        recent_detections = cursor.fetchall()

        stats = {
            "farmers": total_farmers,
            "crops": total_crops,
            "diseases": total_diseases,
            "detections": total_detections
        }

        return render_template(
            "admin.html",
            stats=stats,
            detections=recent_detections
        )

    except Exception as error:
        app.logger.exception("Admin dashboard error: %s", error)
        flash("Unable to load admin dashboard.", "danger")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# --------------------------------------------------
# ADMIN: FARMER MANAGEMENT
# --------------------------------------------------

@app.route("/admin/farmers")
@admin_required
def admin_farmers():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, phone, created_at
            FROM users
            WHERE role = 'farmer'
            ORDER BY created_at DESC
            """
        )

        farmers = cursor.fetchall()

        return render_template(
            "admin_farmers.html",
            farmers=farmers
        )

    except Exception as error:
        app.logger.exception("Farmer management error: %s", error)
        flash("Unable to load farmers.", "danger")
        return redirect(url_for("admin"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# --------------------------------------------------
# ADMIN: DELETE FARMER
# --------------------------------------------------

@app.route(
    "/admin/farmers/<int:farmer_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_farmer(farmer_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s AND role = 'farmer'
            """,
            (farmer_id,)
        )

        if not cursor.fetchone():
            flash("Farmer account not found.", "warning")
            return redirect(url_for("admin_farmers"))

        cursor.execute(
            "DELETE FROM detections WHERE user_id = %s",
            (farmer_id,)
        )

        cursor.execute(
            """
            DELETE FROM users
            WHERE id = %s AND role = 'farmer'
            """,
            (farmer_id,)
        )

        connection.commit()

        flash(
            "Farmer account and its detection records deleted.",
            "success"
        )

    except Exception as error:

        if connection is not None:
            connection.rollback()

        app.logger.exception("Delete farmer error: %s", error)

        flash("Unable to delete farmer account.", "danger")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    return redirect(url_for("admin_farmers"))


# --------------------------------------------------
# ADMIN: CROP MANAGEMENT
# --------------------------------------------------

@app.route("/admin/crops", methods=["GET", "POST"])
@admin_required
def admin_crops():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            crop_name = request.form.get(
                "crop_name", ""
            ).strip()

            description = request.form.get(
                "description", ""
            ).strip()

            if not crop_name:
                flash("Enter a crop name.", "warning")
                return redirect(url_for("admin_crops"))

            cursor.execute(
                """
                INSERT INTO crops (crop_name, description)
                VALUES (%s, %s)
                """,
                (crop_name, description)
            )

            connection.commit()

            flash("Crop added successfully.", "success")

            return redirect(url_for("admin_crops"))

        cursor.execute(
            "SELECT * FROM crops ORDER BY crop_name"
        )

        crops = cursor.fetchall()

        return render_template(
            "admin_crops.html",
            crops=crops
        )

    except Exception as error:

        if connection is not None:
            connection.rollback()

        app.logger.exception("Crop management error: %s", error)

        flash(
            "Unable to manage crops. Check whether the crop already exists.",
            "danger"
        )

        return redirect(url_for("admin"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# --------------------------------------------------
# ADMIN: DISEASE MANAGEMENT
# --------------------------------------------------

@app.route("/admin/diseases", methods=["GET", "POST"])
@admin_required
def admin_diseases():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        if connection is None:
            raise RuntimeError("Database connection failed.")

        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            disease_name = request.form.get(
                "disease_name", ""
            ).strip()

            crop_name = request.form.get(
                "crop_name", ""
            ).strip()

            symptoms = request.form.get(
                "symptoms", ""
            ).strip()

            treatment = request.form.get(
                "treatment", ""
            ).strip()

            prevention = request.form.get(
                "prevention", ""
            ).strip()

            if not all([
                disease_name,
                crop_name,
                symptoms,
                treatment,
                prevention
            ]):
                flash("Complete all disease fields.", "warning")
                return redirect(url_for("admin_diseases"))

            cursor.execute(
                """
                INSERT INTO diseases
                (
                    disease_name,
                    crop_name,
                    symptoms,
                    treatment,
                    prevention
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    disease_name,
                    crop_name,
                    symptoms,
                    treatment,
                    prevention
                )
            )

            connection.commit()

            flash(
                "Disease information added successfully.",
                "success"
            )

            return redirect(url_for("admin_diseases"))

        cursor.execute(
            """
            SELECT *
            FROM diseases
            ORDER BY crop_name, disease_name
            """
        )

        diseases = cursor.fetchall()

        cursor.execute(
            "SELECT crop_name FROM crops ORDER BY crop_name"
        )

        crops = cursor.fetchall()

        return render_template(
            "admin_diseases.html",
            diseases=diseases,
            crops=crops
        )

    except Exception as error:

        if connection is not None:
            connection.rollback()

        app.logger.exception("Disease management error: %s", error)

        flash(
            "Unable to manage disease information.",
            "danger"
        )

        return redirect(url_for("admin"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# --------------------------------------------------
# AI FARMING CHATBOT
# --------------------------------------------------

@app.route("/chatbot", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def chatbot():

    if "user_id" not in session:
        flash(
            "Please login to use AI Farming Assistant.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":

        question = request.form.get(
            "message", ""
        ).strip()

        if not question:
            flash(
                "Please enter your farming question.",
                "warning"
            )
            return redirect(url_for("chatbot"))

        if len(question) > 2000:
            flash(
                "Please keep your question under 2000 characters.",
                "warning"
            )
            return redirect(url_for("chatbot"))

        history = session.get("chat_history", [])

        messages = history[-10:] + [
            {
                "role": "user",
                "content": question
            }
        ]

        try:
            answer = get_farming_answer(messages)

            history.append({
                "role": "user",
                "content": question
            })

            history.append({
                "role": "assistant",
                "content": answer
            })

            session["chat_history"] = history[-12:]
            session.modified = True

        except Exception as error:
            app.logger.exception("Chatbot error: %s", error)

            flash(
                "Unable to get an AI response. Check your API key and connection.",
                "danger"
            )

        return redirect(url_for("chatbot"))

    return render_template(
        "chatbot.html",
        chat_history=session.get("chat_history", [])
    )


# --------------------------------------------------
# CLEAR CHAT HISTORY
# --------------------------------------------------

@app.route("/clear-chat", methods=["POST"])
def clear_chat():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    session.pop("chat_history", None)

    flash("Chat history cleared.", "success")

    return redirect(url_for("chatbot"))


# --------------------------------------------------
# WEATHER AND FARMING ADVICE
# --------------------------------------------------

@app.route("/weather", methods=["GET", "POST"])
def weather():

    if "user_id" not in session:
        flash(
            "Please login to view weather information.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    weather_data = None
    farming_advice = []

    if request.method == "POST":

        location = request.form.get(
            "location", ""
        ).strip()

        if not location:
            flash("Please enter a location.", "warning")
            return redirect(url_for("weather"))

        try:
            weather_data = get_weather(location)

            farming_advice = get_farming_advice(
                weather_data
            )

        except requests.RequestException:
            flash(
                "Weather service is unavailable. Please try again.",
                "danger"
            )

        except ValueError as error:
            flash(str(error), "warning")

        except Exception as error:
            app.logger.exception("Weather route error: %s", error)

            flash(
                "Unable to load weather information.",
                "danger"
            )

    return render_template(
        "weather.html",
        weather=weather_data,
        farming_advice=farming_advice
    )


# --------------------------------------------------
# FARMER ANALYTICS
# --------------------------------------------------

@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        flash(
            "Please login to view analytics.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    analytics_data = get_farmer_analytics(
        session["user_id"]
    )

    if analytics_data is None:

        flash(
            "Unable to load analytics data.",
            "danger"
        )

        analytics_data = {
            "total_scans": 0,
            "healthy_count": 0,
            "diseased_count": 0,
            "disease_labels": [],
            "disease_values": [],
            "month_labels": [],
            "month_values": [],
            "crop_labels": [],
            "crop_values": []
        }

    return render_template(
        "analytics.html",
        analytics=analytics_data
    )


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "error.html",
        error_code=404,
        error_title="Page Not Found",
        error_message="The page you requested does not exist."
    ), 404


@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "error.html",
        error_code=413,
        error_title="File Too Large",
        error_message="Please upload an image smaller than 5 MB."
    ), 413


@app.errorhandler(500)
def server_error(error):

    return render_template(
        "error.html",
        error_code=500,
        error_title="Server Error",
        error_message="Something went wrong. Please try again later."
    ), 500


@app.errorhandler(CSRFError)
def handle_csrf_error(error):

    app.logger.error(
        "CSRF ERROR: %s",
        error.description
    )

    return (
        "CSRF Error: Your form token is missing or expired. "
        "Refresh the page and try again.",
        400
    )
from backend.database import get_db_connection
from werkzeug.security import check_password_hash

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute(
    "SELECT email, password, role FROM users WHERE email=%s",
    ("goskulamallesh@gmail.com",)
)

user = cursor.fetchone()

print("User found:", user is not None)

if user:
    print("Role:", user["role"])
    print("Hash length:", len(user["password"]))
    test_password = input("Enter the new password: ")
    print("Password matches:", check_password_hash(user["password"], test_password))

cursor.close()
conn.close()

# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
