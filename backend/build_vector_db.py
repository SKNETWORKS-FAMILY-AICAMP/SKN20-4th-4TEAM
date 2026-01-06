import os
import pickle
import warnings
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

warnings.filterwarnings("ignore")
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY 없음! .env 확인해줘")

# 문서 로드
with open("chunked_documents.pkl", "rb") as f:
    docs = pickle.load(f)

print(f"로드된 청킹 문서 수: {len(docs)}")

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

persist_dir = "./chroma_startup_all"

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embedding_model,
    collection_name="startup_all_rag",
    persist_directory=persist_dir,
)

print("데이터 벡터DB 생성")
print(f"저장 위치: {persist_dir}")
