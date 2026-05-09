# 智扫通机器人智能客服系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.0-green.svg)](https://python.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 项目简介

智扫通是一个基于 LangChain 和 LangGraph 构建的智能客服系统，专门为扫地机器人提供智能化的问答服务。系统采用 ReAct (Reasoning + Acting) 架构，能够理解用户意图、调用工具获取信息，并生成准确、专业的回答。

### 核心功能

- 🤖 **智能问答**：基于 RAG (检索增强生成) 技术，提供准确的扫地机器人相关知识问答
- 🌤️ **天气查询**：集成天气 API，支持实时天气和天气预报查询
- 📊 **报告生成**：根据用户使用记录生成详细的维护和使用报告
- 💬 **多轮对话**：支持上下文关联的多轮对话，提供更自然的交互体验
- 👤 **用户管理**：支持多用户会话隔离和历史记录管理
- 🔍 **意图识别**：自动识别用户意图并选择合适的工具进行处理

## 🏗️ 技术架构

### 核心技术栈

- **Web 框架**: Streamlit 1.32.0
- **Agent 框架**: LangChain + LangGraph
- **向量数据库**: ChromaDB
- **大语言模型**: 通义千问 (阿里云百炼)
- **MCP 协议**: Model Context Protocol 集成
- **数据处理**: Pandas, PyYAML

### 系统架构图

```
┌─────────────────────────────────────────────┐
│           Streamlit Web Interface           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          ReactAgent (ReAct Pattern)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Intent   │→ │ Task     │→ │ Tool     │  │
│  │ Recogn.  │  │ Planning │  │ Execution│  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │  RAG   │ │ Weather│ │ Report │
   │ Service│ │  API   │ │Generator│
   └────────┘ └────────┘ └────────┘
        │
        ▼
   ┌────────┐
   │ChromaDB│
   └────────┘
```

## 📁 项目结构

```
D:\PythonProject2/
├── agent/                  # Agent 核心模块
│   ├── react_agent.py     # ReAct Agent 实现
│   └── tools/             # 工具集
│       ├── agent_tools.py # 工具定义
│       └── middleware.py  # 中间件
├── rag/                    # RAG 模块
│   ├── rag_service.py     # RAG 服务
│   └── vector_store.py    # 向量存储
├── model/                  # 模型工厂
│   └── factory_model.py   # 模型工厂类
├── config/                 # 配置文件
│   ├── agent.yml          # Agent 配置
│   ├── chroma.yml         # ChromaDB 配置
│   ├── prompts.yml        # Prompt 配置
│   └── rag.yml            # RAG 配置
├── prompts/                # Prompt 模板
│   ├── main_prompt.txt    # 主 Prompt
│   ├── rag_summarize.txt  # RAG 总结 Prompt
│   └── report_prompt.txt  # 报告生成 Prompt
├── utils/                  # 工具类
│   ├── config_handler.py  # 配置处理
│   ├── file_handler.py    # 文件处理
│   ├── logger_handler.py  # 日志处理
│   └── prompt_loader.py   # Prompt 加载器
├── DATA/                   # 数据目录
│   ├── chat_history/      # 聊天历史记录
│   ├── external/          # 外部数据
│   └── *.txt/pdf          # 知识库文档
├── logs/                   # 日志文件
├── chroma_db/             # 向量数据库
├── app.py                  # 主应用入口
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 配置
└── docker-compose.yml     # Docker Compose 配置
```

## 🚀 快速开始

### 前置要求

- Python 3.11+
- pip (Python 包管理器)
- 通义千问 API Key (阿里云百炼)
- LangSmith API Key (可选，用于追踪)

### 安装步骤

1. **克隆仓库**

```bash
git clone <your-repository-url>
cd PythonProject2
```

2. **创建虚拟环境**（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

```bash
# 复制示例配置文件
cp env.example .env

# 编辑 .env 文件，填入你的 API Key
# LANGCHAIN_API_KEY="your-langchain-api-key-here"
# QIANWEN_API_KEY="your-qianwen-api-key-here"
# MCP_SERVER_URL="your-mcp-server-url"
# MCP_API_KEY="your-mcp-api-key-here"
```

5. **准备知识库数据**

将扫地机器人相关文档放入 `DATA/` 目录，支持的格式包括：
- TXT 文本文件
- PDF 文档
- CSV 数据文件

6. **运行应用**

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动。

### Docker 部署

1. **构建镜像**

```bash
docker build -t zhisaotong-agent .
```

2. **运行容器**

```bash
docker run -d \
  -p 8501:8501 \
  -e LANGCHAIN_API_KEY=your-key \
  -e QIANWEN_API_KEY=your-key \
  --name zhisaotong \
  zhisaotong-agent
```

或使用 Docker Compose：

```bash
docker-compose up -d
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `LANGCHAIN_API_KEY` | LangSmith API Key | 是 |
| `QIANWEN_API_KEY` | 通义千问 API Key | 是 |
| `MCP_SERVER_URL` | MCP 服务器地址 | 否 |
| `MCP_API_KEY` | MCP API Key | 否 |

### 配置文件

- **config/agent.yml**: Agent 行为配置
- **config/chroma.yml**: ChromaDB 连接和集合配置
- **config/prompts.yml**: Prompt 模板配置
- **config/rag.yml**: RAG 检索参数配置

## 📝 使用指南

### 基本使用

1. 打开浏览器访问 `http://localhost:8501`
2. 在左侧边栏输入用户 ID 并确认
3. 在底部输入框输入问题，例如：
   - "扫地机器人如何充电？"
   - "今天北京的天气怎么样？"
   - "请生成我的使用报告"

### 功能示例

#### 1. 知识库问答

```
用户：扫地机器人的滤网多久更换一次？
助手：根据维护手册建议，扫地机器人的滤网建议每 2-3 个月更换一次...
```

#### 2. 天气查询

```
用户：上海今天的天气如何？
助手：上海今天晴转多云，气温 18-25°C，东南风 3-4 级...
```

#### 3. 报告生成

```
用户：请根据我的使用记录生成一份详细报告
助手：📊 智扫通使用报告
   用户ID: xxx
   统计周期: xxx
   使用次数: xxx
   ...
```

## 🔧 开发指南

### 添加新工具

1. 在 `agent/tools/agent_tools.py` 中定义工具函数
2. 使用 `@tool` 装饰器标注
3. 在 Agent 初始化时注册工具

```python
from langchain.tools import tool

@tool
def my_custom_tool(query: str) -> str:
    """工具描述"""
    # 实现逻辑
    return result
```

### 自定义 Prompt

编辑 `prompts/` 目录下的模板文件，或修改 `config/prompts.yml` 配置。

### 扩展知识库

1. 将新文档放入 `DATA/` 目录
2. 重启应用，系统会自动向量化新文档
3. 或通过代码手动触发向量化：

```python
from rag.vector_store import VectorStore
store = VectorStore()
store.add_documents(["path/to/new/document.txt"])
```

## 🧪 测试

运行自动化测试：

```bash
pytest parttest/ -v
```

生成测试报告：

```bash
pytest parttest/ --cov=. --cov-report=html
```

## 📊 监控与追踪

项目集成了 LangSmith 用于监控和调试：

1. 访问 [LangSmith](https://smith.langchain.com/)
2. 查看项目 "智扫通智能客服" 的追踪记录
3. 分析 Agent 执行流程和性能

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://python.langchain.com/) - LLM 应用开发框架
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent 编排框架
- [Streamlit](https://streamlit.io/) - Web 应用框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [阿里云百炼](https://dashscope.console.aliyun.com/) - 通义千问大模型

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：[your-email@example.com]

---

**注意**: 本项目仅供学习和研究使用，请遵守相关法律法规和 API 使用条款。
