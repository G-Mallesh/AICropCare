from backend.database import get_db_connection


def test_database_connection():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        if connection is None:
            print("Database connection failed.")
            return False

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        if result and result[0] == 1:
            print("Database connection successful!")
            return True

        print("Database query failed.")
        return False

    except Exception as error:
        print(f"Database connection error: {error}")
        return False

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


if __name__ == "__main__":
    test_database_connection()