import os, json
import config_data
from typing import Sequence, List
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory

# 通过BaseChatMessageHistory类创建一个FileChatMessageHistory类
class FileChatMessageHistory(BaseChatMessageHistory):
    """Json存储会话记录"""

    def __init__(self, session_id: str, storage_path: str):
        self.session_id = session_id    # 会话ID
        self.storage_path = storage_path    # 存储路径
        # 完整的文件路径
        self.file_path = os.path.join(self.storage_path, self.session_id)
    
        # 确保文件夹是存在的
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    # 添加一条消息
    def add_messages(self, message: Sequence[BaseMessage]) -> None:
        all_messages = list(self.messages)  # 已有的消息列表
        all_messages.extend(message)   # 添加新的消息

        # 将消息写入文件中
        # 类对象写入文件是一堆二进制，为了方便查看转成字典，然后由json模块转成字符串
        new_messages = []
        for message in all_messages:
            d = message_to_dict(message)
            new_messages.append(d)
        # 将消息写入文件中
        with open(self.file_path, "w", encoding='utf-8') as f:
            json.dump(new_messages, f, ensure_ascii=False, indent=4)
    
    @property # 装饰器，将messages方法变成一个属性使用
    def messages(self) -> List[BaseMessage]:
        try:
            with open(self.file_path, "r", encoding='utf-8') as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, "w", encoding='utf-8') as f:
            json.dump([], f)

def get_history(session_id):
    return FileChatMessageHistory(session_id, storage_path=config_data.chat_history_path)