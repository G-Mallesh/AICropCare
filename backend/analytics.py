from backend.database import get_db_connection


def get_farmer_analytics(user_id):

    connection = get_db_connection()

    if not connection:
        return None

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # Total scans and healthy/diseased counts
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_scans,
                SUM(
                    CASE
                        WHEN LOWER(disease_name) LIKE '%healthy%'
                        THEN 1 ELSE 0
                    END
                ) AS healthy_count,
                SUM(
                    CASE
                        WHEN LOWER(disease_name) LIKE '%healthy%'
                        THEN 0 ELSE 1
                    END
                ) AS diseased_count
            FROM detections
            WHERE user_id = %s
            """,
            (user_id,)
        )

        summary = cursor.fetchone() or {}

        # Detection counts by disease
        cursor.execute(
            """
            SELECT disease_name, COUNT(*) AS total
            FROM detections
            WHERE user_id = %s
            GROUP BY disease_name
            ORDER BY total DESC
            LIMIT 10
            """,
            (user_id,)
        )

        disease_rows = cursor.fetchall()

        # Monthly detection counts for the current year
        cursor.execute(
            """
            SELECT
                DATE_FORMAT(created_at, '%Y-%m') AS month_key,
                COUNT(*) AS total
            FROM detections
            WHERE user_id = %s
              AND YEAR(created_at) = YEAR(CURDATE())
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month_key
            """,
            (user_id,)
        )

        monthly_rows = cursor.fetchall()

        # Crop detection counts
        cursor.execute(
            """
            SELECT crop_name, COUNT(*) AS total
            FROM detections
            WHERE user_id = %s
            GROUP BY crop_name
            ORDER BY total DESC
            LIMIT 10
            """,
            (user_id,)
        )

        crop_rows = cursor.fetchall()

        return {
            "total_scans": int(summary.get("total_scans") or 0),
            "healthy_count": int(summary.get("healthy_count") or 0),
            "diseased_count": int(summary.get("diseased_count") or 0),
            "disease_labels": [
                row["disease_name"] for row in disease_rows
            ],
            "disease_values": [
                int(row["total"]) for row in disease_rows
            ],
            "month_labels": [
                row["month_key"] for row in monthly_rows
            ],
            "month_values": [
                int(row["total"]) for row in monthly_rows
            ],
            "crop_labels": [
                row["crop_name"] for row in crop_rows
            ],
            "crop_values": [
                int(row["total"]) for row in crop_rows
            ]
        }

    except Exception as error:
        print("Analytics error:", error)
        return None

    finally:
        if cursor:
            cursor.close()
        connection.close()