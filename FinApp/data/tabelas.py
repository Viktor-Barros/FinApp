
import os
import sqlite3
import random
from datetime import datetime, timedelta

# Caminho do banco (deve ser o mesmo usado no seu script de transações)
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "database.db")

# Metas fictícias e seus alcances de valor alvo
metas_ficticias = {
    'Viagem para a Praia': {'min_mult': 2.0, 'max_mult': 4.0},
    'Reserva de Emergência': {'min_mult': 3.0, 'max_mult': 6.0},
    'Comprar Carro Novo': {'min_mult': 10.0, 'max_mult': 20.0},
    'Pagar Dívida': {'min_mult': 1.0, 'max_mult': 3.0},
    'Curso de Inglês': {'min_mult': 0.5, 'max_mult': 1.5},
}

# Conectar ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Buscar todos os usuários e suas rendas (renda será usada para definir o valor alvo)
    # Assumindo que a tabela de usuários se chama TB_Usuario e a coluna de ID é id_usuario
    cursor.execute("SELECT id_usuario, renda FROM TB_Usuario")
    usuarios = cursor.fetchall()
    
    # Se houver usuários, prossegue
    if not usuarios:
        print("Nenhum usuário encontrado na TB_Usuario. Não foram inseridas metas.")
    else:
        for user_id, renda in usuarios:
            
            # Seleciona um número aleatório de metas (entre 1 e 3)
            num_metas = random.randint(1, 3)
            
            # Evita duplicar o nome da meta para o mesmo usuário
            metas_escolhidas = random.sample(list(metas_ficticias.keys()), min(num_metas, len(metas_ficticias)))
            
            for nome_meta in metas_escolhidas:
                meta_info = metas_ficticias[nome_meta]
                
                # Cálculo do valor alvo (multiplica a renda por um fator aleatório)
                valor_alvo = round(random.uniform(meta_info['min_mult'] * renda, meta_info['max_mult'] * renda), 2)
                
                # Valor atual (começa em 0 ou com um pequeno valor aleatório)
                valor_atual = round(random.uniform(0, valor_alvo * 0.1), 2)
                
                # Data final aleatória (entre 6 e 36 meses a partir de hoje)
                dias_prazo = random.randint(180, 1080)
                data_final = (datetime.now() + timedelta(days=dias_prazo)).date().isoformat()
                
                descricao = f'Meta de longo prazo: {nome_meta}'

                # Insere a meta no banco de dados
                cursor.execute("""
                    INSERT INTO TB_Metas (id_usuario, nome, valor_alvo, valor_atual, data_final, descricao)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, nome_meta, valor_alvo, valor_atual, data_final, descricao))

        conn.commit()
        print(f"Metas fictícias inseridas com sucesso para {len(usuarios)} usuários!")

except sqlite3.OperationalError as e:
    # Isso geralmente acontece se a tabela TB_Metas não existir
    print(f"ERRO: A tabela TB_Metas pode não existir no banco de dados. Mensagem: {e}")
    conn.rollback()
except Exception as e:
    conn.rollback()
    print("Erro ao inserir metas:", e)

finally:
    cursor.close()
    conn.close()