"""
    完整性校验任务
"""
from integrity_checker import start_scheduler
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config

db = Chroma(
    collection_name=config.collection_name,
    embedding_function=DashScopeEmbeddings(model="text-embedding-v4"),
    persist_directory=config.persist_directory, 
)

start_scheduler(db)