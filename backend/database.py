from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from sqlalchemy import text


DB_USER = "root"
DB_PASSWORD = "root1234"
DB_HOST = "host.docker.internal"
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

# --- [추가] 연결 테스트 함수 ---
def test_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ [성공] MySQL과 파이썬이 성공적으로 연결되었습니다!")
            return True
    except Exception as e:
        print(f"❌ [실패] 연결 오류 발생: {e}")
        return False
#------------------------------ 여기까지 연결

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


# --- [테스트 실행] ---
if __name__ == "__main__":
    test_db_connection()

if __name__ == "__main__":
    try:
        # 1. 테스트용 유저 생성
        print("1. 테스트 유저 생성 중...")
        new_user_id = create_user("test@example.com", "password123")
        print(f"✅ 유저 생성 완료! (ID: {new_user_id})")

        # 2. 테스트용 채팅 세션 생성
        print("2. 채팅 세션 생성 중...")
        session_id = create_chat_session(new_user_id)
        print(f"✅ 세션 생성 완료! (ID: {session_id})")

        # 3. 테스트용 채팅 로그 저장
        print("3. 채팅 로그 저장 중...")
        save_chat(session_id, "user", "안녕하세요, DB 연결 테스트입니다.")
        save_chat(session_id, "assistant", "네, 연결이 아주 잘 되었습니다!")
        print("✅ 채팅 로그 저장 완료!")

        print("\n🎉 모든 테스트가 성공했습니다! 이제 챗봇에 연결하세요.")

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")