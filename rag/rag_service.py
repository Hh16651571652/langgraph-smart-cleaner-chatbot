"""总结服务类，用户提问，将提问和参考资料提交给模型，让模型总结回复"""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from model.factory_model import chat_model
from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompt

class RagSummerizeService:
    def __init__(self):
        self.vectors_store=VectorStoreService()
        self.retriever=self.vectors_store.get_retriever()
        self.prompt_text=load_rag_prompt()
        self.prompt_template=PromptTemplate.from_template(self.prompt_text)
        self.model=chat_model
        self.chain=self._init_chain ()
    def _init_chain(self):
        chain=self.prompt_template|self.model|StrOutputParser()
        return chain
    def retriever_docs(self,question:str)->list[Document]:
        docs=self.retriever.invoke(question)
        return docs
    def rag_summarize(self,question:str)->str:
        context_docs=self.retriever_docs(question)
        context=""
        counter=0
        for doc in context_docs:
            counter+=1
            context+=f"[参考资料{counter}]:参考资料:{doc.page_content}|参考元数据:{doc.metadata}\n"
        return self.chain.invoke({"input":question,"context":context})

if __name__=="__main__":
    rag_summerize_service=RagSummerizeService()
    print(rag_summerize_service.rag_summarize("小户型适合那种扫地机器人？"))
