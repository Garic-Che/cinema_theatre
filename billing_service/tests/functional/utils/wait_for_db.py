import os
import sys
import time
import psycopg2


def wait_for_postgres():
    db_url = os.getenv("DB_URL")
    max_retries = 10
    retry_delay = 5

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            print(f"PostgreSQL not ready ({i+1}/{max_retries}): {e}")
            time.sleep(retry_delay)

    print("Failed to connect to PostgreSQL")
    return False


if __name__ == "__main__":
    if not wait_for_postgres():
        sys.exit(1)
