"""
基于streamlit完成WEB网页上传服务
"""
import streamlit as st
import time
from knowledge_base import KnowledgeBaseServer
from security import FileSecurityScanner
from file_preprocessing import  process_text

# 添加网页标题
st.title('知识库更新服务')

# 添加上传文件组件
uploaded_file = st.file_uploader(
    "请上传txt/docx/pdf/xlsx文件",
    type = ['txt', 'docx', 'pdf', 'xlsx'],
    accept_multiple_files = False   # 不允许上传多个文件
)

# session_state是一个字典，用于解决st状态丢失的问题。如果不写，类对象是会丢失的
if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseServer()

# 如果文件不为空
if uploaded_file is not None:
    # 提取文件信息
    file_name = uploaded_file.name
    file_type = uploaded_file.name.split('.')[-1].lower()
    file_size = uploaded_file.size / 1024   # 单位转为KB

    # 相当于二级标题
    st.subheader(f"文件名称: {file_name}")
    st.write(f"格式: {file_type} | 文件大小: {file_size:.2f}KB")

    # 扫描文件是否安全
    scanner = FileSecurityScanner()
    if scanner.scan_uploaded_file(uploaded_file):
        # 获取文件内容，类型是bytes，通过decode转为字符串
        from file_preprocessing import process_text
        try:
            text = process_text(uploaded_file)
            st.write(text)
        except Exception as e:
            st.error(str(e))
            st.stop()

        with st.spinner("正在上传文件..."):     # 在spinner内会有加载动画
            time.sleep(1)
            result = st.session_state["service"].upload_by_str(text, file_name, file_type)
            st.write(result)
    else:
        st.error("文件异常，禁止上传")