from sqlalchemy import create_engine, text

DB_USER = "root"
DB_PASSWORD = "newpassword123"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "startup_chatbot"

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    echo=False
)

def save_chat(role: str, content: str):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_log (role, content)
                VALUES (:role, :content)
            """),
            {"role": role, "content": content}
        )
        conn.commit()
