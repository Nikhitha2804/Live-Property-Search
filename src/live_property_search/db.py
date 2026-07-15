import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()


def get_db_connection():
    """Create and return a database connection with optimized settings."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL is not set')
        return None
    try:
        conn = psycopg2.connect(
            database_url,
            client_encoding='utf8',
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        # Set connection-level performance parameters
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


if __name__ == '__main__':
    conn = get_db_connection()
    if conn:
        print('CONNECTED')
        conn.close()
    else:
        print('FAILED')
