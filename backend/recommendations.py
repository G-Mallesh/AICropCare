from backend.database import get_db_connection


def get_disease_recommendation(disease_name):
    connection = get_db_connection()

    if not connection:
        return None

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # Example: Tomato___Early_blight -> Early blight
        parts = disease_name.split("___")
        clean_name = parts[-1].replace("_", " ").strip()

        cursor.execute(
            """
            SELECT disease_name, crop_name, symptoms,
                   treatment, prevention
            FROM diseases
            WHERE LOWER(disease_name) = LOWER(%s)
            LIMIT 1
            """,
            (clean_name,)
        )

        result = cursor.fetchone()

        if not result:
            cursor.execute(
                """
                SELECT disease_name, crop_name, symptoms,
                       treatment, prevention
                FROM diseases
                WHERE LOWER(disease_name) LIKE LOWER(%s)
                LIMIT 1
                """,
                (f"%{clean_name}%",)
            )
            result = cursor.fetchone()

        return result

    except Exception as error:
        print("Recommendation error:", error)
        return None

    finally:
        if cursor:
            cursor.close()
        connection.close()