import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load .env file from a specific path
load_dotenv("/home/student3/email.env")

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def create_query_executor(connection, dictionary=False):
    """
    Create a database query executor for executing SQL queries.
    Returns a query executor object that can execute SQL and fetch results.
    """
    return connection.cursor(dictionary=dictionary)