"""
知识库
"""
import os
import config_data as config
import hashlib
import json
import numpy as np
import re 
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from integrity_checker import create_snapshot

def check_md5(md5_str: str):
    """
        检查传入的md5字符串是否已经被处理过了
        return False(md5字符串没有被处理过) True(md5字符串已经被处理过)
    """
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()     # 去掉换行符、空格
            if line == md5_str:
                return True     # 已经被处理过
            
        return False

def save_md5(md5_str: str):
    """保存md5字符串保存到本地文件中"""
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')

def get_string_md5(input_str: str, encoding='utf-8'):
    """获取字符串的md5"""
    
    # 将字符串转换为bytes字节数组
    str_bytes = input_str.encode(encoding=encoding)

    # 创建md5对象
    md5_obj = hashlib.md5()     # 得到md5对象
    md5_obj.update(str_bytes)   # 传入bytes对象
    md5_hex = md5_obj.hexdigest()   # 得到md5的十六进制字符串，不管字符串多大，计算结果都是32位

    return md5_hex

class KnowledgeBaseServer(object):
    """知识库类"""
    def __init__(self):
        # 如果文件夹不存在则创建，存在则跳过
        os.makedirs(config.persist_directory, exist_ok=True)
        self.embeddings = DashScopeEmbeddings(model=config.embedding_model)
        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embeddings,
            persist_directory=config.persist_directory,     # 数据库本地存储路径
        )  # 向量存储的实例Chroma向量库对象

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = config.first_chunk_size, 
            chunk_overlap = config.chunk_overlap,
            separators = config.separators,  # 分割符
            length_function = len
        )     # 文本分割器对象 

        self.fine_spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.second_chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len
        )

    # 分批embedding
    def batch_embed(self, texts, batch_size=50):
        vectors = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            vectors.extend(self.embeddings.embed_documents(batch))
        return vectors

    # 基于语义相似度的文本分块
    def semantic_split(self, text: str, threshold=config.threshold): # threshold：相似度阈值，越小切得越碎
        # 先按句子切
        sentences = re.split(r'(。|！|？)', text)

        # 重新拼接标点
        new_sentences = []
        for i in range(0, len(sentences)-1, 2):
            sentence = (sentences[i] + sentences[i+1]).strip()
            if sentence:
                new_sentences.append(sentence)

        # 处理最后一个没有标点的句子
        if len(sentences) % 2 != 0:
            last_sentence = sentences[-1].strip()
            if last_sentence:
                new_sentences.append(last_sentence)

        sentences = new_sentences

        if len(sentences) <= 1:
            return [text]

        # 计算 embedding
        embeddings = self.batch_embed(sentences)

        # 定义余弦相似度
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        # 开始拼 chunk
        chunks = []
        current_chunk = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = cosine_similarity(embeddings[i-1], embeddings[i])

            if sim < threshold:
                # 语义变化大 → 切断
                chunks.append("。".join(current_chunk))
                current_chunk = [sentences[i]]
            else:
                # 语义相近 → 合并
                current_chunk.append(sentences[i])

        # 最后一块
        if current_chunk:
            chunks.append("。".join(current_chunk))

        return chunks

    def semantic_split_with_limit(self, text: str):
        """
        两阶段分块：
        1. 先粗切
        2. 再语义分块
        3. 最后长度兜底
        """

        final_chunks = []

        # Step1：先粗切（关键）
        rough_chunks = self.spliter.split_text(text)

        for rough_chunk in rough_chunks:
            # Step2：对小块做语义分块
            semantic_chunks = self.semantic_split(rough_chunk)

            for chunk in semantic_chunks:
                # Step3：长度兜底
                if len(chunk) > config.second_chunk_size:
                    sub_chunks = self.fine_spliter.split_text(chunk)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(chunk)

        return final_chunks
    
    # 按照结构划分文本
    def split_by_top_level(self, text: str, min_length=config.min_length):
        """
        只按一级标题（1. 2. 3.）切分
        """

        # 匹配一级标题：1. xxx（不包含 1.1）
        pattern = r'(\n?\d+\.\s+.*)'

        parts = re.split(pattern, text)

        chunks = []
        current_chunk = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # 如果是一级标题（关键：不能是1.1）
            if re.match(r'^\d+\.\s+', part):
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk += "\n" + part

        if current_chunk:
            chunks.append(current_chunk.strip())

        # 🔥 可选：合并过小chunk（防止太碎）
        final_chunks = []
        buffer = ""

        for chunk in chunks:
            if len(chunk) < min_length:
                buffer += "\n" + chunk
            else:
                if buffer:
                    chunk = buffer + "\n" + chunk
                    buffer = ""
                final_chunks.append(chunk)

        if buffer:
            final_chunks.append(buffer)

        return final_chunks
    
    # 标题增强
    def enhance_chunks(self, chunks):
        enhanced = []
        for chunk in chunks:
            title = chunk.split("\n")[0]
            enhanced.append(f"{title}\n{chunk}")
        return enhanced
    
    def final_split(self, text: str):
        chunks = self.split_by_top_level(text)   # ✅ 一级标题切分
        chunks = self.enhance_chunks(chunks)     # ✅ 标题增强（可选但强烈建议）
        return chunks

    def get_meatdata(self, data: str):
        """利用大模型获取文档元数据"""
        chat_template = ChatPromptTemplate.from_messages(
            [
                ("system", config.metadata_prompt),
                ("user", "文本：{input}")
            ]
        )
        model = ChatTongyi(model=config.chat_model,api_key=config.api_key)
        result = model.invoke(chat_template.format_prompt(input=data))
        return json.loads(result.content)

    def upload_by_str(self, data: str, filename, flieype):
        """将传入的字符串，进行向量化，存入向量数据库中"""
        md5_hex = get_string_md5(data)

        if (check_md5(md5_hex)):
            return "[跳过]内容已经存在知识库中"
        
        if len(data) > config.max_split_chat_num:
            knowledge_chunks = self.final_split(data)    # 传字符串就行了，返回一个列表
            create_snapshot(md5_hex, knowledge_chunks)
        else:
            knowledge_chunks = [data]
            create_snapshot(md5_hex, knowledge_chunks)

        # 基础 metadata
        base_metadata = {
            "file_name": filename,
            "file_type": flieype,
            "document_id": md5_hex,
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "管理员"
        } | (self.get_meatdata(data) or {})

        metadatas = []

        for idx, chunk in enumerate(knowledge_chunks):
            chunk_metadata = base_metadata.copy()

            chunk_metadata.update({
                "chunk_md5": md5_hex,
                "chunk_id": idx,
                "chunk_total": len(knowledge_chunks),
            })

            metadatas.append(chunk_metadata)

        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=metadatas
        )

        # 保存md5
        save_md5(md5_hex)

        return "[成功]内容已经成功上传载入向量库"