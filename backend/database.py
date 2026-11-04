import mysql.connector
from config import Config


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )

        return connection

    except mysql.connector.Error as error:
        print("Database Connection Error:", error)
        return None


def execute_query(query, values=None, fetch=False):
    connection = get_db_connection()

    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(query, values or ())

        if fetch:
            result = cursor.fetchall()
            return result

        connection.commit()
        return True

    except mysql.connector.Error as error:
        print("SQL Error:", error)
        connection.rollback()
        return None

    finally:
        cursor.close()
        connection.close()