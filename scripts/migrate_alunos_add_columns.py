import os
import sqlite3
from models import DATABASE_URL, create_database_tables

def db_path_from_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return os.path.abspath(url.replace("sqlite:///", ""))
    return os.path.abspath(url)

def table_columns(conn: sqlite3.Connection, table: str) -> set:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return {row[1] for row in cur.fetchall()}

def add_column(conn: sqlite3.Connection, table: str, col_def: str):
    sql = f"ALTER TABLE {table} ADD COLUMN {col_def}"
    conn.execute(sql)

def main():
    db_path = db_path_from_url(DATABASE_URL)
    if not os.path.exists(db_path):
        print(f"Arquivo DB não encontrado em: {db_path}")
        print("Se for um projeto em desenvolvimento, pode recriar o DB removendo o arquivo e executando o sistema.")
        return

    conn = sqlite3.connect(db_path)
    try:
        cols = table_columns(conn, "alunos")
        to_add = {
            "telefone": "telefone TEXT DEFAULT ''",
            "responsavel": "responsavel TEXT DEFAULT ''",
            "graduacao": "graduacao TEXT DEFAULT ''",
            # se quiser garantir presença das colunas de cpf/formato (ajuste conforme seu model)
            "cpf_formatado": "cpf_formatado TEXT DEFAULT ''",
            "cpf_limpo": "cpf_limpo TEXT DEFAULT ''",
        }
        added = False
        for name, defn in to_add.items():
            if name not in cols:
                print(f"Adicionando coluna: {name}")
                add_column(conn, "alunos", defn)
                added = True
            else:
                print(f"Coluna já existe: {name}")
        if added:
            conn.commit()
            print("Alterações aplicadas no DB.")
        else:
            print("Nenhuma alteração necessária.")
    finally:
        conn.close()

    # Garante que outras tabelas (novas) sejam criadas se necessário
    try:
        create_database_tables()
        print("create_database_tables() executado (demais tabelas criadas/atualizadas).")
    except Exception as e:
        print("Aviso: falha ao rodar create_database_tables():", e)

if __name__ == "__main__":
    main()