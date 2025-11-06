# run_local.py

import subprocess
import os

# --- INFORMAÇÃO DE REDE DO SEU PC (FIXA) ---
# Se o seu IP mudar, você terá que atualizar este arquivo.
LOCAL_IP = "192.168.200.103"
PORT = os.environ.get('FLASK_RUN_PORT', 20243)

if __name__ == '__main__':
    
    print("-" * 50)
    print("--- SERVIDOR FLASK INICIANDO ---")
    print(f"ACESSO LOCAL (Seu PC): http://127.0.0.1:{PORT}/login")
    
    # Este é o link que seu amigo usa (Apenas se estiverem na mesma Wi-Fi)
    print(f"ACESSO NA REDE LOCAL (Seu Amigo): http://{LOCAL_IP}:{PORT}/login")
    print("-" * 50)
    
    # Define a variável de ambiente HOST para 0.0.0.0 para garantir a abertura da porta
    os.environ['FLASK_RUN_HOST'] = '0.0.0.0' 
    
    # Executa o app.py
    try:
        # Nota: Usaremos FLASK_APP=app.py e flask run, que é o método padrão
        # e mais robusto do Flask, em vez de 'python app.py'
        subprocess.run(['flask', 'run'], check=True)
    except FileNotFoundError:
        print("\nERRO: O comando 'flask' não foi encontrado. Certifique-se de que o ambiente virtual está ativo e o Flask está instalado.")
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao iniciar o servidor Flask: {e}")