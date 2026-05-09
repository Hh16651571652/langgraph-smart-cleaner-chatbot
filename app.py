import time
import os
import json
from datetime import datetime
import streamlit as st
from agent.react_agent import ReactAgent
from utils.path_tool import get_abs_path
from utils.logger_handler import logger

# 在文件开头设置环境变量
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
# 从环境变量读取API密钥，避免硬编码敏感信息
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
if not langchain_api_key:
    raise EnvironmentError(
        "未找到LANGCHAIN_API_KEY环境变量。请设置环境变量或创建.env文件。\n"
        "示例：export LANGCHAIN_API_KEY='your-api-key-here'"
    )
os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = "智扫通智能客服"

# 设置页面标题
st.title('智扫通机器人智能客服')
st.divider()

# 初始化 session state
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# 将session_state注入到全局变量中，供工具函数使用
import builtins
builtins.session_state = st.session_state

# 从文件加载历史消息
def load_chat_history():
    """从文件加载历史消息，增加异常处理以提高健壮性"""
    if not st.session_state.user_id:
        return []
        
    base_path = get_abs_path("DATA/chat_history")
    user_dir = os.path.join(base_path, st.session_state.user_id)
    session_file = os.path.join(user_dir, f"{st.session_state.session_id}.json")
    
    if not os.path.exists(session_file):
        return []
    
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 验证数据格式
            if not isinstance(data, list):
                logger.warning(f"[load_chat_history] 文件格式错误，期望数组但得到 {type(data)}")
                return []
            return [{"role": msg["role"], "content": msg["content"]} for msg in data]
    except json.JSONDecodeError as e:
        # JSON解析失败，记录错误并返回空列表
        logger.error(f"[load_chat_history] JSON解析失败: {str(e)}，文件可能已损坏")
        # 备份损坏的文件
        backup_file = session_file + ".corrupted"
        try:
            os.rename(session_file, backup_file)
            logger.info(f"[load_chat_history] 已备份损坏的文件到: {backup_file}")
        except Exception:
            pass
        return []
    except Exception as e:
        # 其他未知错误
        logger.error(f"[load_chat_history] 加载历史记录失败: {str(e)}")
        return []

# 恢复消息状态 - 从文件加载
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# 创建容器（必须在所有可能重绘的代码之前）
chat_container = st.container()
input_container = st.container()

# 侧边栏 - 用户ID输入和确认
with st.sidebar:
    st.header("👤 用户设置")
    
    # 用户ID输入（侧边栏）
    user_id_input = st.text_input("请输入您的用户ID:", value=st.session_state.user_id)
    
    if st.button("确认用户ID"):
        if user_id_input.strip():
            old_user_id = st.session_state.user_id
            st.session_state.user_id = user_id_input.strip()
            
            # 切换用户时重新加载历史记录
            st.session_state.messages = load_chat_history()
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.success(f"用户ID已更新为: {st.session_state.user_id}")
            st.rerun()
        else:
            st.warning("请输入有效的用户ID")

# 首先显示聊天内容（在最前面）
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 检查用户ID是否已设置
    if not st.session_state.user_id:
        st.info("请在左侧边栏输入并确认您的用户ID以开始对话")
        # 如果没有用户ID，不进行后续处理
        st.stop()

# 然后处理AI回复生成（在聊天内容之后，但在输入框之前）
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        # 检查是否有对应的AI回复
        has_reply = False
        for j in range(i+1, len(st.session_state.messages)):
            if st.session_state.messages[j]["role"] == "assistant":
                has_reply = True
                break
        
        # 如果没有回复且尚未开始生成，则启动生成
        if not has_reply and f"generating_{i}" not in st.session_state:
            st.session_state[f"generating_{i}"] = True
            
            # 立即重新运行，让界面先显示"思考中..."
            st.rerun()

# 只有当需要生成AI回复时才执行
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        has_reply = False
        for j in range(i+1, len(st.session_state.messages)):
            if st.session_state.messages[j]["role"] == "assistant":
                has_reply = True
                break
        
        if not has_reply and f"generating_{i}" in st.session_state:
            with chat_container:
                with st.chat_message("assistant"):
                    try:
                        # 显示正在思考状态
                        thinking_placeholder = st.empty()
                        thinking_placeholder.markdown("智慧助手正在思考中....")
                        
                        response_messages = []
                        res_stream = st.session_state.agent.execute_stream(
                            message["content"],
                            user_id=st.session_state.user_id,
                            session_id=st.session_state.session_id
                        )
                        
                        def capture(generator, cache_list):
                            # 先清除"正在思考"状态
                            thinking_placeholder.empty()
                            
                            for chunk in generator:
                                cache_list.append(chunk)
                                for char in chunk:
                                    time.sleep(0.01)
                                    yield char
                    
                        full_response = st.write_stream(capture(res_stream, response_messages))
                        
                        # 添加AI回复
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response
                        })
                        
                        # 清除生成标志
                        if f"generating_{i}" in st.session_state:
                            del st.session_state[f"generating_{i}"]
                            
                        # 保存到文件
                        base_path = get_abs_path("DATA/chat_history")
                        user_dir = os.path.join(base_path, st.session_state.user_id)
                        os.makedirs(user_dir, exist_ok=True)
                        session_file = os.path.join(user_dir, f"{st.session_state.session_id}.json")
                        
                        data = []
                        for msg in st.session_state.messages:
                            if msg["role"] == "user":
                                data.append({"role": "user", "content": msg["content"], "timestamp": datetime.now().isoformat()})
                            elif msg["role"] == "assistant":
                                data.append({"role": "assistant", "content": msg["content"], "timestamp": datetime.now().isoformat()})
                        
                        with open(session_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            
                    except Exception as e:
                        # 清除正在思考状态
                        if 'thinking_placeholder' in locals():
                            thinking_placeholder.empty()
                            
                        error_msg = f"发生错误：{str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        if f"generating_{i}" in st.session_state:
                            del st.session_state[f"generating_{i}"]
                    
                    # 重新运行以刷新界面
                    st.rerun()

# 最后显示输入区域（在最后面）
with input_container:
    st.divider()  # 分隔线
    
    # 底部输入区域
    col1, col2 = st.columns([4, 1])
    
    with col1:
        prompt = st.chat_input("请输入您的问题", key="chat_input", disabled=not st.session_state.user_id)
    
    with col2:
        # 报告按钮直接作为用户输入
        report_disabled = not st.session_state.user_id
        if st.button("📊 报告", key="report_btn", disabled=report_disabled):
            # 直接添加到消息历史
            st.session_state.messages.append({
                "role": "user",
                "content": "请根据我的使用记录生成一份详细报告"
            })
            st.rerun()
    
    # 处理普通聊天输入
    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        st.rerun()


