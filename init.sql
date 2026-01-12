-- 1. 창고(DB) 만들기
CREATE DATABASE IF NOT EXISTS startup_chatbot
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 2. 권한 설정 및 비밀번호 방식 변경
-- root 계정이 외부(도커 내부망)에서도 접속 가능하게 설정
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'root1234';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- 3. 창고 선택
USE startup_chatbot;

-- 4. 유저 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 채팅 세션 테이블 생성
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 6. 채팅 로그 테이블 생성
CREATE TABLE IF NOT EXISTS chat_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    source_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);