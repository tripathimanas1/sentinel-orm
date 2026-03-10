from clickhouse_driver import Client
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("CLICKHOUSE_USER", "default")
password = os.getenv("CLICKHOUSE_PASSWORD", "")
host = os.getenv("CLICKHOUSE_HOST", "localhost")
port = int(os.getenv("CLICKHOUSE_PORT", 9000))

print(f"Connecting to {host}:{port} as {user} with password length {len(password)}")

try:
    client = Client(host=host, port=port, user=user, password=password)
    result = client.execute("SELECT 1")
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
