"""
Extract & Load: Neon (PostgreSQL) -> BigQuery

Ten skrypt jest uruchamiany przez GitHub Actions (patrz .github/workflows/load.yml).
Zmienne środowiskowe (NEON_CONNECTION_STRING, BQ_PROJECT_ID, BQ_DATASET)
są ustawiane w kroku workflow, na podstawie GitHub Secrets.
"""

import os
import psycopg2
import pandas as pd
from google.cloud import bigquery

# ============================================================
# KONFIGURACJA
# ============================================================

NEON_CONNECTION_STRING = os.environ["NEON_CONNECTION_STRING"]
BQ_PROJECT_ID = os.environ["BQ_PROJECT_ID"]
BQ_DATASET = os.environ["BQ_DATASET"]
# BQ_TABLE nie jest już potrzebne jako pojedyncza zmienna, jeśli używamy listy poniżej

# Lista tabel w dokładnej kolejności sekwencyjnego ładowania:
TABLES_TO_LOAD = [
    "cars",
    "employees",
    "customers",
    "models",
    "transactions",
    "test_drive",
]

# Kolumna używana do wykrywania nowych/zmienionych wierszy przy incremental load
# (Zakłada, że każda z powyższych tabel ma kolumnę 'updated_at')
INCREMENTAL_COLUMN = "updated_at"

# "full_refresh" -> zawsze ładuje wszystko od nowa (nadpisuje tabelę w BigQuery)
# "incremental"  -> ładuje tylko wiersze nowsze niż ostatnio załadowane
LOAD_MODE = "incremental"

# ============================================================
# LOGIKA
# ============================================================


def get_last_loaded_timestamp(bq_client: bigquery.Client, table_ref: str):
    """Odczytuje maksymalny timestamp już obecny w tabeli docelowej BigQuery."""
    query = f"SELECT MAX({INCREMENTAL_COLUMN}) AS max_ts FROM `{table_ref}`"
    try:
        result = bq_client.query(query).result()
        row = next(iter(result))
        return row.max_ts
    except Exception:
        return None


def extract_from_neon(source_table: str, mode: str, last_ts=None) -> pd.DataFrame:
    """Łączy się z bazą Neon i wyciąga dane z podanej tabeli źródłowej."""
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    try:
        if mode == "incremental" and last_ts is not None:
            query = f"SELECT * FROM {source_table} WHERE {INCREMENTAL_COLUMN} > %s"
            df = pd.read_sql(query, conn, params=(last_ts,))
        else:
            query = f"SELECT * FROM {source_table}"
            df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df


def load_to_bigquery(bq_client: bigquery.Client, df: pd.DataFrame, table_ref: str, mode: str):
    """Ładuje DataFrame do BigQuery."""
    write_disposition = (
        bigquery.WriteDisposition.WRITE_TRUNCATE
        if mode == "full_refresh"
        else bigquery.WriteDisposition.WRITE_APPEND
    )
    job_config = bigquery.LoadJobConfig(write_disposition=write_disposition)
    job = bq_client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Blokuje wykonanie, dopóki ta tabela się nie załaduje (gwarancja sekwencyjności)
    return job


def main():
    bq_client = bigquery.Client()

    for table_name in TABLES_TO_LOAD:
        print(f"\n--- Rozpoczynam przetwarzanie tabeli: {table_name} ---")
        table_ref = f"{BQ_PROJECT_ID}.{BQ_DATASET}.{table_name}"

        last_ts = None
        if LOAD_MODE == "incremental":
            last_ts = get_last_loaded_timestamp(bq_client, table_ref)
            print(f"[{table_name}] Ostatni załadowany timestamp w BigQuery: {last_ts}")

        df = extract_from_neon(table_name, LOAD_MODE, last_ts)
        print(f"[{table_name}] Wyciągnięto {len(df)} wierszy z Neon")

        if df.empty:
            print(f"[{table_name}] Brak nowych danych do załadowania -- pomijam.")
            continue

        job = load_to_bigquery(bq_client, df, table_ref, LOAD_MODE)
        print(f"[{table_name}] Załadowano {job.output_rows} wierszy do {table_ref} (tryb: {LOAD_MODE})")


if __name__ == "__main__":
    main()
