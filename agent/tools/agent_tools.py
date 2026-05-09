import asyncio
import os.path
from datetime import datetime
import csv

from langchain.agents import create_agent
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from model.factory_model import chat_model
from utils.config_handler import agent_conf, rag_conf
from langchain_core.tools import tool
from utils.logger_handler import logger
from rag.rag_service import RagSummerizeService
from utils.path_tool import get_abs_path
client = MultiServerMCPClient({"mcp-M2UzYzE5MmMyYzIy": {
            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/mcp-M2UzYzE5MmMyYzIy/mcp",
            "headers": {
                "Authorization": "Bearer sk-a6c5f90acfeb4af4b6364e87df6be599"
            }, "transport": "http"
        }})
rag = RagSummerizeService()
user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05",
           "2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
external_data = {}

@tool(description="从向量存储中检索参考资料")
def rag_summarize(query:str)->str:
    return rag.rag_summarize(query)

@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    async def get_weather_async(city: str) -> str:
        tools = await client.get_tools()
        llm = ChatOpenAI(model=rag_conf["chat_model_name"],
                         api_key=os.getenv("QIANWEN_API_KEY"),
                         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云百炼兼容接口
                         )

        # 直接在 prompt 中使用 today 变量
        today = datetime.now().strftime("%Y-%m-%d")  # 直接获取当前日期

        prompt = ChatPromptTemplate.from_messages(
            [("system", "你是一个天气预报助手，调用工具[tools]获取今日{today}、城市:{city}的天气，将天气信息总结为:'北京的天气是晴天，气温 26 摄氏度，空气湿度 50%，南风一级，AQI 指数 21'的格式并返回"),
             ("system", "{agent_scratchpad}")])
        agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools)
        response = await agent_executor.ainvoke({"city": city, "today": today})
        return response["output"]
    return asyncio.run(get_weather_async(city))

@tool(description="根据用户的id，获取用户所在城市的名称，以纯字符串形式返回")
def get_city(user_id: str) -> str:
    """根据用户ID 从 records.csv 中读取对应的城市地址"""
    try:
        external_data_path = get_abs_path(agent_conf["external_data_path"])
        if not os.path.exists(external_data_path):
            logger.error(f"[get_city] 外部数据文件{external_data_path}不存在")
            return "未获取到用户的地区信息"
        with open(external_data_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["用户ID"].strip('"') == user_id.strip():
                    city = row["地区"].strip('"')
                    logger.info(f"[get_city] 用户{user_id}所在城市：{city}")
                    return city
        
        logger.warning(f"[get_city] 未找到用户{user_id}的地址信息")
        return "未获取到用户的地区信息"
    except Exception as e:
        logger.error(f"[get_city] 读取城市信息失败：{str(e)}")
        return "未获取到用户的地区信息"

@tool(description="无入参，从Web会话中获取当前用户的唯一标识（ID字符串），ID格式为数字字符串（如\"1001\"）")
def user_id_from_session() -> str:
    """从session state中获取当前用户的ID"""
    from utils.path_tool import get_session_state
    session_state = get_session_state()
    user_id = session_state.get("user_id", "")
    logger.info(f"[user_id_from_session] 获取到当前用户ID：{user_id}")
    return user_id

@tool(description="获取指定月份，支持相对时间。入参relative默认为'current'表示当前月，'last'表示上个月，或传入数字字符串如'-1'表示前一个月")
def get_target_month(relative: str = "current") -> str:
    """获取目标月份，支持相对时间计算"""
    from dateutil.relativedelta import relativedelta
    
    now = datetime.now()
    if relative == "current":
        target = now
    elif relative == "last":
        target = now - relativedelta(months=1)
    else:
        try:
            # 解析数字偏移，如 '-2' 表示两个月前
            offset = int(relative)
            target = now + relativedelta(months=offset)
        except ValueError:
            logger.warning(f"[get_target_month] 无效的参数: {relative}，默认返回当前月")
            target = now

    month_str = target.strftime("%Y-%m")

    # 检查是否在数据范围内（2025年）
    if not month_str.startswith("2025-"):
        logger.warning(f"[get_target_month] 月份 {month_str} 超出数据范围(2025年)，返回空字符串")
        return ""

    logger.info(f"[get_target_month] 参数:{relative}, 返回月份:{month_str}")
    return month_str

@tool(description="无入参，调用后触发中间件自动为报告生成场景动态注入上下文信息，为后续提示词切换提供上下文支撑")
def fill_context_for_report():
    """触发报告生成上下文注入"""
    logger.info("[fill_context_for_report] 开始执行上下文注入")
    return "fill_context_for_report 已调用"

def generate_external_data():
    """从CSV文件生成外部数据字典"""
    global external_data
    if not external_data:  # 只在为空时加载
        external_data = {}  # 重置字典
        external_data_path = get_abs_path(agent_conf["external_data_path"])
        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

        with open(external_data_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_id = row["用户ID"].strip('"')
                month = row["时间"].strip('"')
                if user_id not in external_data:
                    external_data[user_id] = {}
                external_data[user_id][month] = {
                    "特征": row["特征"].strip('"'),
                    "效率": row["清洁效率"].strip('"'),
                    "消耗": row["耗材"].strip('"'),
                    "对比": row["对比"].strip('"')
                }
        logger.info(f"[generate_external_data] 成功加载 {len(external_data)} 个用户的外部数据")

@tool(description="从外部系统中获取用户的使用记录，以纯字符串形式返回，如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    """根据用户ID和月份获取使用记录"""
    try:
        generate_external_data()  # 确保数据已加载

        if user_id in external_data and month in external_data[user_id]:
            record = external_data[user_id][month]
            result = f"""
用户ID: {user_id}
月份: {month}
使用特征: {record['特征']}
清洁效率: {record['效率']}
耗材情况: {record['消耗']}
与同类用户对比: {record['对比']}
""".strip()
            logger.info(f"[fetch_external_data] 成功获取用户{user_id}在{month}的记录")
            return result
        else:
            logger.warning(f"[fetch_external_data] 未找到用户{user_id}在{month}的记录")
            return ""
    except Exception as e:
        logger.error(f"[fetch_external_data] 获取记录失败: {str(e)}")
        return ""

if __name__=="__main__":
    print(fetch_external_data("1001","2025-01"))