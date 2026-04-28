import streamlit as st
import config_data as config
from rag import RagService
from security import PromptSecurityChecker

# 标题
st.title("客服问答系统")
st.divider()    # 分隔符

# 选择角色
if "role" not in st.session_state:
    st.session_state["role"] = None   # 默认角色

# 记录/展示角色
role = st.radio(
    "选择角色",
    ["客服", "PM", "管理员"],
    index=None
)

# 如果选了，才写入 session
if role is not None:
    st.session_state["role"] = role
st.write("当前角色：", st.session_state["role"])

# 如果还没选，直接阻断
if st.session_state["role"] is None:
    st.warning("请先选择角色")
    st.stop()

# 记录历史消息
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "你好，有什么可以帮助你"}]

# 没有RAG对象或角色被改变时创建RAG对象
if (
    "rag" not in st.session_state 
    or st.session_state.get("rag_role") != st.session_state["role"]
):
    st.session_state["rag"] = RagService(st.session_state["role"])
    st.session_state["rag_role"] = st.session_state["role"]

# 遍历消息列表，将消息显示在页面上
for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

# 在页面最下方提供用户输入栏
prompt = st.chat_input()

# prompt 安全检测器
checker = PromptSecurityChecker()

if prompt:
    # 在页面输出用户的提问
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    # prompt 安全检测
    if checker.check_prompt(prompt) == "HIGH":
        st.error(checker.enforce(prompt))
    elif checker.check_prompt(prompt) == "MIDDLE":
        st.warning(checker.enforce(prompt))
        ai_res = []
        with st.spinner("AI思考中……"):
            res_stream = st.session_state["rag"].chain.stream({"input": prompt}, config=config.session_config)

            # 这个函数目的在于解决，使用流式输出时，将迭代器中的内容捕获为string，从而支持历史信息保存
            def capture(generator, cache_list):
                for chunk in generator:
                    cache_list.append(chunk)
                    yield chunk     # 依然返回迭代器

            st.chat_message("assistant").write_stream(capture(res_stream, ai_res))
            st.session_state["messages"].append({"role": "assistant", "content": "".join(ai_res)})
    else:
        ai_res = []
        with st.spinner("AI思考中……"):
            res_stream = st.session_state["rag"].chain.stream({"input": prompt}, config=config.session_config)

            # 这个函数目的在于解决，使用流式输出时，将迭代器中的内容捕获为string，从而支持历史信息保存
            def capture(generator, cache_list):
                for chunk in generator:
                    cache_list.append(chunk)
                    yield chunk     # 依然返回迭代器

            st.chat_message("assistant").write_stream(capture(res_stream, ai_res))
            st.session_state["messages"].append({"role": "assistant", "content": "".join(ai_res)})
