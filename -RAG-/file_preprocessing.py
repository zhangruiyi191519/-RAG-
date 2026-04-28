"""
文件预处理，包含以下两种功能：
1. 不同格式文件解析
2. 文件质量预处理
"""
from pypdf import PdfReader
from docx import Document
import pandas as pd
import io


# 文件解析总函数
def extract_text(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()

    if file_type == "txt":
        return extract_txt(uploaded_file)

    elif file_type == "pdf":
        return extract_pdf(uploaded_file)

    elif file_type == "docx":
        return extract_docx(uploaded_file)

    elif file_type == "xlsx":
        return extract_xlsx(uploaded_file)

    else:
        raise ValueError("不支持的文件类型")

# 解析txt
def extract_txt(uploaded_file):
    return uploaded_file.getvalue().decode("utf-8")

# 解析pdf
def extract_pdf(uploaded_file):
    pdf = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    text = ""

    for page in pdf.pages:
        text += page.extract_text() or ""

    return text

# 解析docx
def extract_docx(uploaded_file):
    doc = Document(io.BytesIO(uploaded_file.getvalue()))
    return "\n".join([p.text for p in doc.paragraphs])

# 解析xlsx，舍弃表格结构
def extract_xlsx(uploaded_file):
    xls = pd.ExcelFile(io.BytesIO(uploaded_file.getvalue()))
    text = ""

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)

        text += f"【Sheet: {sheet_name}】\n"
        text += df.to_string(index=False)
        text += "\n\n"

    return text

# 文本质量预处理总函数
def process_text(uploaded_file):
    # 提取文本
    text = extract_text(uploaded_file)

    # 清洗
    text = clean_text(text)

    # 校验
    validate_text(text)

    return text

# 去除空行，删除首位空格，按照换行符分割
def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    return "\n".join(cleaned_lines)

# 乱码检测
def is_garbled(text: str) -> bool:
    if not text:
        return True

    total_chars = len(text)
    weird_chars = 0

    for ch in text:
        # 中文 + 英文 + 常见符号
        if not (
            '\u4e00' <= ch <= '\u9fff' or   # 中文
            'a' <= ch.lower() <= 'z' or     # 英文
            ch.isdigit() or
            ch in ".,。，!??？！;:()[]{}-_'\" \n"
        ):
            weird_chars += 1

    ratio = weird_chars / total_chars

    return ratio > 0.3   # 超过30%认为是乱码

# 文本有效性检测
def validate_text(text: str):
    if not text or len(text.strip()) < 20:
        raise ValueError("文本内容过少，请检查文件")

    if is_garbled(text):
        raise ValueError("检测到文本可能为乱码，请检查文件编码或内容")