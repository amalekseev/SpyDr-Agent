from sqlalchemy import create_engine, text

CONN_STR = "postgresql+psycopg2://postgres:mypassword@localhost:5488/postgres"

try:
    engine = create_engine(CONN_STR)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Соединение с SQLAlchemy установлено успешно!")
except Exception as e:
    print(f"SQLAlchemy не смог подключиться: {e}")