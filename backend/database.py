from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from sqlalchemy import text


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

# 비밀번호 해쉬 검증
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# 사용자 조회
def get_user_by_email(email: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT user_id, email, password_hash
                FROM users
                WHERE email = :email
            """),
            {"email": email}
        )
        return result.fetchone()

# 유저 생성
def create_user(email: str, password: str):
    password_hash = hash_password(password)
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                INSERT INTO users (email, password_hash)
                VALUES (:email, :password_hash)
            """),
            {"email": email, "password_hash": password_hash}
        )
        conn.commit()
        return result.lastrowid

# 채팅 세션
def create_chat_session(user_id=None):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                INSERT INTO chat_sessions (user_id)
                VALUES (:user_id)
            """),
            {"user_id": user_id}
        )
        conn.commit()
        return result.lastrowid

# 채팅 로그 저장
def save_chat(session_id, role, content, source_type=None):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_log (session_id, role, content, source_type)
                VALUES (:sid, :role, :content, :source)
            """),
            {
                "sid": session_id,
                "role": role,
                "content": content,
                "source": source_type
            }
        )
        conn.commit()

