# 📋 客服问答系统 (Customer Service Q&A System)

## 🌟 项目简介

这是一个基于 **RAG (Retrieval-Augmented Generation)** 架构的智能客服问答系统，采用 Streamlit 构建 Web 界面，支持多角色权限管理、文件安全扫描、知识库管理和智能对话功能。系统能够处理多种文档格式（TXT、PDF、DOCX、XLSX），并通过向量检索技术为用户提供准确、可追溯的答案。

## ✨ 核心特性

### 🔐 多层安全防护
- **文件安全扫描**：集成 Windows Defender 对上传文件进行病毒扫描
- **提示词安全检测**：三级风险等级（高/中/低）识别和拦截恶意 Prompt 注入攻击
- **数据完整性校验**：基于 SHA256 签名的快照机制，防止知识库数据被篡改
- **定时完整性检查**：每日自动执行数据一致性验证并报警

### 👥 多角色权限管理
- **客服角色**：仅可访问公开级别（public）知识
- **PM 角色**：可访问公开和内部级别（public + internal）知识
- **管理员角色**：可访问所有级别（public + internal + secret）知识

### 📚 智能知识库管理
- **多格式支持**：支持 TXT、PDF、DOCX、XLSX 文件格式解析
- **智能文本分块**：两阶段分块策略（一级标题切分 + 语义相似度分块）
- **标题增强**：自动提取并增强文档标题上下文
- **去重机制**：基于 MD5 的内容去重，避免重复入库
- **元数据自动提取**：利用大模型自动生成文档摘要和元数据

### 🤖 RAG 检索增强生成
- **相邻片段扩展**：自动获取相关 chunk 的前后文片段，提升上下文完整性
- **流式输出**：支持实时流式回答，提升用户体验
- **对话历史管理**：基于文件的会话持久化存储
- **来源追溯**：每个答案都标注来源文件和原文引用

### 🛡️ 文本质量预处理
- **乱码检测**：自动识别并拒绝乱码文件（异常字符比例 > 30%）
- **内容有效性校验**：过滤过短或无效文本
- **智能清洗**：去除空行、首尾空格等噪声

## 🏗️ 技术架构
┌─────────────────────────────────────────────┐
│           Streamlit Web Interface            │
│   (app_qa.py / app_file_upload.py)          │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐         ┌──────▼────────┐
│ Security│        │  RAG Service  │
│ Module  │        │   (rag.py)    │
└─────────┘        └──────┬────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
     ┌────────▼────────┐    ┌─────────▼────────┐
     │ Vector Store    │    │ Chat History     │
     │ (Chroma DB)     │    │ (File Storage)   │
     └────────┬────────┘    └──────────────────┘
              │
     ┌────────▼────────┐
     │ Knowledge Base  │
     │ Server          │
     └────────┬────────┘
              │
     ┌────────▼────────┐
     │ File Preproces- │
     │ sing & Integrity│
     │ Checker         │
     └─────────────────┘
## 📦 主要模块说明

| 模块文件 | 功能描述 |
|---------|---------|
| [app_qa.py](file://c:\Users\86152\Desktop\客服问答系统\app_qa.py) | 问答系统主界面，支持多角色选择和对话交互 |
| [app_file_upload.py](file://c:\Users\86152\Desktop\客服问答系统\app_file_upload.py) | 知识库文件上传和管理界面 |
| [rag.py](file://c:\Users\86152\Desktop\客服问答系统\rag.py) | RAG 服务核心逻辑，包含检索链构建和角色过滤 |
| [knowledge_base.py](file://c:\Users\86152\Desktop\客服问答系统\knowledge_base.py) | 知识库服务器，负责文档分块、嵌入和存储 |
| [vector_stores.py](file://c:\Users\86152\Desktop\客服问答系统\vector_stores.py) | 向量存储服务封装（基于 Chroma） |
| [security.py](file://c:\Users\86152\Desktop\客服问答系统\security.py) | 安全模块，包含文件扫描和提示词检测 |
| [file_preprocessing.py](file://c:\Users\86152\Desktop\客服问答系统\file_preprocessing.py) | 文件解析和文本质量预处理 |
| [integrity_checker.py](file://c:\Users\86152\Desktop\客服问答系统\integrity_checker.py) | 数据完整性校验和快照管理 |
| [file_history_store.py](file://c:\Users\86152\Desktop\客服问答系统\file_history_store.py) | 对话历史持久化存储 |
| [config_data.py](file://c:\Users\86152\Desktop\客服问答系统\config_data.py) | 全局配置文件 |
| [schduler.py](file://c:\Users\86152\Desktop\客服问答系统\schduler.py) | 定时任务调度器 |

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Windows 操作系统（用于 Windows Defender 集成）

### 安装依赖
```bash
pip install streamlit langchain langchain-chroma langchain-community pypdf python-docx pandas openpyxl schedule
