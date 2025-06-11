import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

_client = None
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def get_bq_client():
    """
    Cria e retorna uma instância do cliente oficial do Google BigQuery.
    """
    global _client
    if _client is not None:
        return _client

    project_id = os.getenv("APP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("Erro de configuração: GOOGLE_CLOUD_PROJECT não definido.")

    try:
        print("INFO: Inicializando cliente nativo do BigQuery...")
        _client = bigquery.Client(project=project_id)
        print("INFO: Cliente BigQuery inicializado com sucesso.")
        return _client
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível criar o cliente do BigQuery. Erro: {e}")
        raise