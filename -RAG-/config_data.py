# knowledge_base
md5_path = "C:/Users/86152/Desktop/客服问答系统/md5.text"

# Chroma
collection_name = "konwledge_base"
persist_directory = "C:/Users/86152/Desktop/客服问答系统/chroma_db"

# RecursiveCharacterTextSplitter
first_chunk_size = 1000
second_chunk_size = 600
chunk_overlap = 100
separators = ["\n\n", "\n", ".", "!", "?", " ", "。", "！", "？"]
max_split_chat_num = 500
min_length = 150
threshold = 0.90

# VectorStoreService
similarity_threshold = 5

# model
chat_model = "qwen3-max"
embedding_model = "text-embedding-v4"
api_key="sk-f9579e89f34e46d287c9bc6aa9ea5b6f"

# ChatHistory
chat_history_path = "C:/Users/86152/Desktop/客服问答系统/chat_history"

# session_config
session_config = {
    "configurable":{
        "session_id": "user_001"
    }
}

# security
exe_path='C:/Program Files/Windows Defender/MpCmdRun.exe'
HIGH_RISK_PATTERNS = [
    r"忽略.*指令",
    r"ignore.*instructions",
    r"无视.*规则",
    r"you are now",
    r"act as",
    r"系统提示词",
    r"system prompt",
    r"管理员",
    r"访问数据库",
    r"输出所有",
    r"必须执行",
    r"do not refuse",
    r"调用.*函数",
]
MIDDLE_RISK_PATTERNS = [
    r"你可以尝试",
    r"建议你",
    r"假设你是",
    r"尽可能多",
    r"补充所有",
    r"优先考虑",
    r"这段内容很重要",
    r"你能访问",
]
middle_risk_patterns_examples = "你可以尝试、建议你、假设你是、尽可能多、补充所有、优先考虑、这段内容很重要、你能访问……"
high_risk_patterns_examples = "忽略指令、无视规则、you are now、act as、系统提示词、系统提示词、管理员、访问数据库……"

# permission
ROLE_PERMISSIONS = {
    "客服": ["public"],
    "PM": ["public", "internal"],
    "管理员": ["public", "internal", "secret"]
}

# prompt
metadata_prompt = """
你需要完成以下任务：

1. 从输入文本中提取元数据字段（如：creator、creation_date、access_level等）。
2. 无论是否提取到其他字段，必须生成一个字段：
   "abstract": "约100字的摘要"

输出要求（非常重要）：
- 只返回 JSON
- 不要输出任何解释、说明或多余内容
- 不要使用 ```json 或 ``` 包裹
- 所有键必须使用双引号
- 如果没有任何字段，也必须返回如下格式：

{{ 
  "abstract": "摘要内容"
}}"""

main_prompt = """
请严格基于提供的参考资料回答问题：

【规则要求】
1. 仅允许使用参考资料中的信息，不得引入任何外部知识或自行推断
2. 回答需简洁、准确、专业
3. 每个结论必须标注来源文件名称
4. 必须附上对应的原文引用（逐字引用，不得修改）
5. 若资料中无相关内容，必须明确回复：“无法从提供的资料中找到答案”
6. 展示每个文件的背景资料（元数据），把字段翻译成中文并整理好格式"""

# integrity_checker
snapshot_path = "C:/Users/86152/Desktop/客服问答系统/snapshot"