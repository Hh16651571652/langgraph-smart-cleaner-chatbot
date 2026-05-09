import os
from abc import ABC, abstractmethod
from typing import Optional
from utils.config_handler import rag_conf
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings

class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self)->Optional[Embeddings|BaseChatModel]:
         pass

class ChatModelFactory(BaseModelFactory):
    def generator(self) ->Optional[Embeddings|BaseChatModel]:
        # 优先使用环境变量，如果没有则使用默认的阿里云 API Key
        api_key = os.getenv("QIANWEN_API_KEY", "sk-a6c5f90acfeb4af4b6364e87df6be599")
        return ChatTongyi(model=rag_conf["chat_model_name"], api_key=api_key)

class EmbeddingModelFactory(BaseModelFactory):
    def generator(self) ->Optional[Embeddings|BaseChatModel]:
        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])

chat_model=ChatModelFactory().generator()
embed_model=EmbeddingModelFactory().generator()
