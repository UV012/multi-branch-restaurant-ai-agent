import psycopg
from sqlalchemy import create_engine, text

print("1. Testing raw psycopg connect...")
try:
    conn = psycopg.connect("postgresql://postgres:postgrespassword@127.0.0.1:5432/restaurant_ai", connect_timeout=5)
    print("RAW_PSYCOPG_CONNECTED!")
    conn.close()
except Exception as e:
    print("RAW_FAILED:", e)

print("2. Testing SQLAlchemy create_engine with psycopg...")
try:
    engine = create_engine(
        "postgresql+psycopg://postgres:postgrespassword@127.0.0.1:5432/restaurant_ai",
        connect_args={"connect_timeout": 5},
    )
    with engine.connect() as conn:
        res = conn.execute(text("SELECT version()"))
        print("SQLALCHEMY_PSYCOPG_CONNECTED:", res.scalar())
except Exception as e:
    print("SQLALCHEMY_FAILED:", e)
