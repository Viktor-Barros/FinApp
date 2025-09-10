# filepath: c:\Users\Gabi\Documents\Dev\Faculdade\APS II\FinApp\FinApp\FinApp\db.py
import mysql.connector

def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="finapp"
        )
    except mysql.connector.Error as err:
        print(f"Erro ao conectar: {err}")
        return None