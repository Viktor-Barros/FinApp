import sqlite3
import os

def get_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    # Pasta fixa "data"
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)  
    db_path = os.path.join(data_dir, "database.db")
    
    print(f"📁 Conectando ao banco de dados: {db_path}")
    return sqlite3.connect(db_path)