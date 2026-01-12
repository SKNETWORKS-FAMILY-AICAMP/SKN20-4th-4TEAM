FROM python:3.10-slim

# 리눅스에서 DB 관련 라이브러리 빌드에 필요한 도구들을 먼저 설치합니다.
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# pip 자체를 먼저 최신으로 업데이트합니다.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]