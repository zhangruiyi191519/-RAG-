import config_data as config
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from typing import List
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from file_history_store import get_history


class RagService(object):
    def __init__(self, role: str):
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model)
        )

        self.prompt_template = ChatPromptTemplate(
            [
                ("system", config.main_prompt),
                ("system", "背景信息：{metadata}"),
                ("system", "参考资料：{context}"),
                ("system", "用户历史对话：{history}"),
                ("user", "请回答问题：{input}")
            ]
        )

        self.chat_model = ChatTongyi(model=config.chat_model)

        self.role = role

        self.chain = self.__get_chain()

    # 获取相邻的chunk，并排序
    def expand_chunks(self, docs: List[Document]) -> List[Document]:
        expanded = []
        seen = set()

        # 👇 记录输入
        self.debug_info = {
            "input_chunks": len(docs),
            "input_ids": [(d.metadata.get("document_id"), d.metadata.get("chunk_id")) for d in docs]
        }

        for doc in docs:
            doc_id = doc.metadata.get("document_id")
            chunk_id = doc.metadata.get("chunk_id")

            if doc_id is None or chunk_id is None:
                continue

            neighbors = self.vector_service.get_neighbors(doc_id, chunk_id)

            for n in neighbors:
                key = (n.metadata.get("document_id"), n.metadata.get("chunk_id"))

                if key not in seen:
                    expanded.append(n)
                    seen.add(key)

        # 排序（建议你用这个）
        expanded.sort(
            key=lambda x: (
                x.metadata.get("document_id"),
                x.metadata.get("chunk_id", 0)
            )
        )

        # 👇 记录输出
        self.debug_info["output_chunks"] = len(expanded)
        self.debug_info["output_ids"] = [
            (d.metadata.get("document_id"), d.metadata.get("chunk_id")) for d in expanded
        ]

        return expanded
    
    # 根据角色过滤chunk
    def filter_by_role(self, docs: List[Document]) -> List[Document]:
        allowed_levels = config.ROLE_PERMISSIONS.get(self.role, ["public"])

        return [
            doc for doc in docs
            if doc.metadata.get("access_level", "public") in allowed_levels
        ]

    def __get_chain(self):      # 这是一个私有方法,不可以从外部调用
        """
            最终的执行链
        """
        retriever = self.vector_service.get_retriever()

        def format_func(docs: List[Document]):
            if not docs:
                return {
                    "context": "无相关参考资料",
                    "metadata": "无背景信息"
                }
            
            context_str = ""
            metadata_str = ""

            for doc in docs:
                # 文本内容
                context_str += f"{doc.page_content}\n"

                # 元数据（格式化）
                for k, v in doc.metadata.items():
                    metadata_str += f"{k}：{v}\n"
                metadata_str += "\n"

            return {
                "context": context_str,
                "metadata": metadata_str
            }

        # 兼容用的函数        
        def format_for_retriever(value: dict) -> str:
            return value["input"]
        
        # 兼容用的函数
        def format_for_prompt_template(value):
            new_value = {}

            new_value["input"] = value["input"]["input"]
            new_value["history"] = value["input"]["history"]
            new_value["context"] = value["context"]["context"]
            new_value["metadata"] = value["context"]["metadata"]
            new_value["role"] = value["input"].get("role", "客服")

            return new_value

        retrieved = (
            RunnableLambda(format_for_retriever)
            | retriever
            | RunnableLambda(self.expand_chunks)
            | RunnableLambda(self.filter_by_role)
            | format_func
        )

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": retrieved
            } | RunnableLambda(format_for_prompt_template) | self.prompt_template | self.chat_model | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key = "input",
            history_messages_key = "history"
        )

        return conversation_chain