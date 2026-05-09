from typing import Generator
import os
import json
from datetime import datetime
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from model.factory_model import chat_model
from agent.tools.agent_tools import (
    rag_summarize,
    get_weather,
    get_city,
    get_target_month, 
    fetch_external_data,
    fill_context_for_report
)
from agent.tools.middleware import *
from utils.path_tool import get_abs_path

tools_name = [
    rag_summarize,
    get_weather,
    get_city,
    get_target_month,
    fetch_external_data,
    fill_context_for_report
]
middleware_name = [
    monitor_tool,
    log_before_model,
    report_prompt_switch
]

class ReactAgent:
    def __init__(self):
        self.base_memory_path = get_abs_path("DATA/chat_history")
        os.makedirs(self.base_memory_path, exist_ok=True)
        
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=tools_name,
            middleware=middleware_name
        )
    
    def _get_session_file(self, user_id: str, session_id: str) -> str:
        """获取会话文件路径"""
        user_dir = os.path.join(self.base_memory_path, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f"{session_id}.json")
    
    def _load_history(self, user_id: str, session_id: str) -> list:
        """加载历史对话"""
        session_file = self._get_session_file(user_id, session_id)
        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                messages = []
                for msg in data:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                return messages
        return []
    
    def _save_history(self, user_id: str, session_id: str, messages: list):
        """保存完整对话历史到文件"""
        session_file = self._get_session_file(user_id, session_id)
        
        data = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                data.append({
                    "role": "user", 
                    "content": msg.content, 
                    "timestamp": datetime.now().isoformat()
                })
            elif isinstance(msg, AIMessage):
                data.append({
                    "role": "assistant", 
                    "content": msg.content, 
                    "timestamp": datetime.now().isoformat()
                })
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _get_default_user_id(self) -> str:
        """获取默认用户ID（Web 场景下从 session 获取）"""
        try:
            import streamlit as st
            if "user_id" in st.session_state:
                return st.session_state.user_id
        except:
            pass
        return "default_user"
    
    def execute_stream(self, query: str, user_id: str = None, session_id: str = None) -> Generator[str, None, None]:
        """流式执行，带持久化记忆"""
        if not user_id:
            user_id = self._get_default_user_id()
        
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 加载历史消息 - 保持原有逻辑
        history = self._load_history(user_id, session_id)
        all_messages = history + [HumanMessage(content=query)]
        
        input_dict = {"messages": all_messages}
        config = {
            "configurable": {
                "session_id": f"{user_id}_{session_id}"
            },
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "project": "智扫通智能客服"
            }
        }
        
        response_message = None
        full_response = ""
        
        # LangSmith会自动追踪，无需上下文管理器
        for chunk in self.agent.stream(input_dict, config=config, stream_mode="values"):
            if isinstance(chunk, dict) and "messages" in chunk:
                messages = chunk["messages"]
                if messages:
                    latest_message = messages[-1]
                    if hasattr(latest_message, "content") and latest_message.content:
                        content = latest_message.content.strip() + "\n"
                        yield content
                        response_message = latest_message
                        full_response += content

        # ✅ 保持原有的手动保存逻辑不变
        if response_message:
            all_messages.append(response_message)
            self._save_history(user_id, session_id, all_messages)

if __name__ == "__main__":
    agent = ReactAgent()
    
    user_id = "1001"
    for chunk in agent.execute_stream("扫地机器人在我所在地区的气温下如何保养", user_id):
        print(chunk, end="", flush=True)
