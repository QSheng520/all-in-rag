import os
# hugging face镜像设置，如果国内环境无法使用启用该设置
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
# 若系统代理访问不了 hugging face，让相关请求绕过代理直连
os.environ.setdefault('NO_PROXY', 'hf-mirror.com,huggingface.co')
os.environ.setdefault('no_proxy', 'hf-mirror.com,huggingface.co')
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings 
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

load_dotenv()

# 使用 AIHubmix
Settings.llm = OpenAILike(
    model="deepseek-flash",
    api_key=os.getenv("CHAT_DEEPSEEK_API_KEY"),
    api_base="https://api.deepseek.com",
    is_chat_model=True
)

# Settings.llm = OpenAI(
#     model="deepseek-chat",
#     api_key=os.getenv("DEEPSEEK_API_KEY"),
#     api_base="https://api.deepseek.com"
# )
Settings.embed_model = HuggingFaceEmbedding("BAAI/bge-small-zh-v1.5")

docs = SimpleDirectoryReader(input_files=["../../data/C1/markdown/easy-rl-chapter1.md"]).load_data()

index = VectorStoreIndex.from_documents(docs)

query_engine = index.as_query_engine()

print(query_engine.get_prompts())

print(query_engine.query("文中举了哪些例子?"))