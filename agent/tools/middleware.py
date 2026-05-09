
from typing import Callable, Dict, List
from collections import defaultdict
import time
from langchain.agents import AgentState
from langchain.agents.middleware import ModelRequest, dynamic_prompt, before_model, wrap_tool_call
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command

from utils.logger_handler import logger
from utils.prompt_loader import load_report_prompt, load_system_prompt

# 全局变量用于跟踪工具调用历史，防止无限循环
# 格式: {session_id: [(tool_name, args_hash, timestamp), ...]}
tool_call_history: Dict[str, List[tuple]] = defaultdict(list)
# 配置参数
MAX_RECENT_CALLS = 50  # 最大保留的最近调用次数
TIME_WINDOW_SECONDS = 300  # 时间窗口（秒），默认5分钟
MAX_SAME_TOOL_CALLS = 3  # 同一工具在时间窗口内最多调用次数


def _check_tool_loop(session_id: str, tool_name: str, args_hash: int, current_time: float) -> bool:
    """
    检查工具调用是否可能导致无限循环
    
    Args:
        session_id: 会话ID
        tool_name: 工具名称
        args_hash: 参数哈希值
        current_time: 当前时间戳
        
    Returns:
        bool: 如果检测到可能的无限循环返回True，否则返回False
    """
    if session_id not in tool_call_history:
        return False
    
    history = tool_call_history[session_id]
    
    # 清理过期的记录
    cutoff_time = current_time - TIME_WINDOW_SECONDS
    recent_calls = [(name, hash_val, ts) for name, hash_val, ts in history if ts > cutoff_time]
    
    # 统计相同工具的调用次数
    same_tool_calls = [call for call in recent_calls if call[0] == tool_name]
    
    # 如果相同工具调用次数超过阈值，认为可能存在循环
    if len(same_tool_calls) >= MAX_SAME_TOOL_CALLS:
        logger.warning(f"[tool loop detection] 会话 {session_id} 中工具 '{tool_name}' 在 {TIME_WINDOW_SECONDS}秒内已调用 {len(same_tool_calls)} 次，超过阈值 {MAX_SAME_TOOL_CALLS}")
        return True
    
    # 检查是否有完全相同的调用（工具名+参数都相同）
    identical_calls = [call for call in recent_calls if call[0] == tool_name and call[1] == args_hash]
    if len(identical_calls) >= MAX_SAME_TOOL_CALLS:
        logger.warning(f"[tool loop detection] 会话 {session_id} 中工具 '{tool_name}' 使用相同参数已调用 {len(identical_calls)} 次")
        return True
    
    return False


def _record_tool_call(session_id: str, tool_name: str, args_hash: int, current_time: float):
    """
    记录工具调用历史
    
    Args:
        session_id: 会话ID
        tool_name: 工具名称
        args_hash: 参数哈希值
        current_time: 当前时间戳
    """
    # 添加到历史记录
    tool_call_history[session_id].append((tool_name, args_hash, current_time))
    
    # 保持历史记录不超过最大限制
    if len(tool_call_history[session_id]) > MAX_RECENT_CALLS:
        # 保留最近的 MAX_RECENT_CALLS 条记录
        tool_call_history[session_id] = tool_call_history[session_id][-MAX_RECENT_CALLS:]
    
    logger.debug(f"[tool history] 会话 {session_id} 记录工具调用: {tool_name}, 当前历史记录数: {len(tool_call_history[session_id])}")


#请求的数据封装，执行的函数本身
@wrap_tool_call
def monitor_tool(request:ToolCallRequest,
                 handler:Callable[[ToolCallRequest],ToolMessage|Command])->ToolMessage|Command:#工具执行的监控
    """监控工具执行，记录工具调用的输入输出和性能指标，并防止无限循环"""
    tool_name = request.tool_call['name']
    tool_args = request.tool_call['args']
    
    # 获取session_id用于追踪
    session_id = None
    try:
        if hasattr(request, 'runtime') and request.runtime:
            session_id = request.runtime.context.get('session_id', 'default')
    except:
        session_id = 'default'
    
    # 计算参数的哈希值用于比较
    args_hash = hash(str(sorted(tool_args.items())) if isinstance(tool_args, dict) else str(tool_args))
    current_time = time.time()
    
    # 检查是否会导致无限循环
    if _check_tool_loop(session_id, tool_name, args_hash, current_time):
        error_msg = f"检测到工具 '{tool_name}' 可能存在无限循环调用，已阻止执行"
        logger.error(f"[tool loop detection] {error_msg}")
        raise RuntimeError(error_msg)
    
    # 记录本次调用
    _record_tool_call(session_id, tool_name, args_hash, current_time)
    
    logger.info(f"[tool monitor] 执行工具:{tool_name}")
    logger.info(f"[tool monitor] 传入参数:{tool_args}")
    try:
        result=handler(request)
        logger.info(f"[tool monitor] 工具:{tool_name} 调用成功")
        if tool_name=="fill_context_for_report":
            request.runtime.context["report"] = True
        return result
    except Exception as e:
        logger.error(f"[tool monitor] 工具:{tool_name} 调用失败，原因:{str(e)}")
        raise e

@before_model
def log_before_model(state:AgentState,
                     runtime:Runtime
                     ):#在模型执行前输出日志
    """在模型执行前输出日志，记录当前状态和上下文信息"""
    logger.info(f"[log before model] 即将调用模型，带有{len(state['messages'])}条信息")
    logger.debug(f"[log before model] 信息:{type(state['messages'][-1]).__name__}{state['messages'][-1].content.strip()}")
    return None

@dynamic_prompt
def report_prompt_switch(request:ModelRequest):#动态切换提示词
    """动态切换提示词，根据上下文选择不同的系统提示词配置"""
    is_report = request.runtime.context.get("report", False) if request.runtime.context else False
    if is_report:#是报告生成场景，返回报告生成提示词内容
        return load_report_prompt()
    return load_system_prompt()
