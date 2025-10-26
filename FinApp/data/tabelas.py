import os
import sqlite3

# Caminho do banco
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "database.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Deletar transações do id 19 ao 26
    cursor.execute("DELETE FROM TB_Transacao WHERE id_transacao BETWEEN ? AND ?", (19, 26))
    conn.commit()
    print("Transações deletadas com sucesso!")
except Exception as e:
    conn.rollback()
    print("Erro ao deletar transações:", e)
finally:
    cursor.close()
    conn.close()
