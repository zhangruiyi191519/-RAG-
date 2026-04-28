"""
返回检索器加入链中
"""
from langchain_chroma import Chroma
import config_data as config

class VectorStoreService:
    def __init__(self, embedding):
        """
        :param embedding: 嵌入模型的传入
        """
        self.embedding = embedding

        self.vector_store = Chroma(
            collection_name=config.collection_name,
            persist_directory=config.persist_directory,
            embedding_function=self.embedding
        )

    def get_retriever(self):
        """
            返回向量检索器，方便加入链
        """
        return self.vector_store.as_retriever( search_kwargs={"k": config.similarity_threshold})
    
    # 获取当前 chunk 的前后片段
    def get_neighbors(self, doc_id: str, chunk_id: int):
        """
        获取当前 chunk 的前后片段（chunk_id-1, chunk_id, chunk_id+1）
        """
        results = self.vector_store.similarity_search(
            query="",   # 这里只是用 filter，不靠相似度
            k=3,
            filter={
                "$and": [
                    {"document_id": doc_id},
                    {"chunk_id": {"$in": [chunk_id - 1, chunk_id, chunk_id + 1]}}
                ]
            }
        )

        return results