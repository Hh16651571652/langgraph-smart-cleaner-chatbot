import os
from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.config_handler import chroma_conf
from model.factory_model import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.file_handler import get_md5_hex, txt_loader, pdf_loader, listdir_with_allowed_type
from utils.path_tool import get_abs_path
from utils.logger_handler import logger


class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=chroma_conf["persist_directory"],
        )
        self.splitter=RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            length_function=len,
            separators=chroma_conf["separators"]
        )
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k":chroma_conf["k"]})
    def load_document(self):
        """从数据文件夹内读取数据文件，转为向量存入向量库
        要计算文件的md5值去重"""
        #检查字符串是否已经存储过
        def check_md5_hex(md5_for_check:str):
            if not os.path.exists(os.path.join(get_abs_path(chroma_conf["md5_hex"]))):
                open(get_abs_path(chroma_conf["md5_hex"]),"w",encoding="utf-8").close()
                return False#md5没处理过
            with open(get_abs_path(chroma_conf["md5_hex"]),"r",encoding="utf-8") as f:
                for line in f.readlines():
                    line=line.strip()
                    if line==md5_for_check:
                        return True#md5处理过了
                return  False
        #保存字符串到md5文件
        def save_md5_hex(md5_for_check:str):
            with open(get_abs_path(chroma_conf["md5_hex"]),"a",encoding="utf-8") as f:
                f.write(md5_for_check+"\n")
        #获取文件对应的document
        def get_file_documents(read_path:str):
            if read_path.endswith("txt"):
                return txt_loader(read_path)
            if read_path.endswith("pdf"):
                return pdf_loader(read_path)
            return []
        allowed_files_path:list[str]=listdir_with_allowed_type(get_abs_path(chroma_conf["data_path"]),allowed_types=tuple(chroma_conf["allow_knowledge_file_type"]))
        for path in allowed_files_path:
            get_file_md5_hex=get_md5_hex(path)
            if check_md5_hex(get_file_md5_hex):
                logger.info(f"[加载知识库]{path}内容已经存在知识库内，跳过")
                continue
            try:
                documents:list[Document]=get_file_documents(path)
                if not documents:
                    logger.warning(f"[加载知识库]{path}没有内容，跳过")
                    continue
                split_documents:list[Document]=self.splitter.split_documents(documents)
                if not split_documents:
                    logger.warning(f"[加载知识库]{path}没有内容，跳过")
                    continue
                #将内容存入向量库中
                self.vector_store.add_documents(split_documents)
                #记录这个已经处理好的文件md5，避免重复加载
                save_md5_hex(get_file_md5_hex)
                logger.info(f"[加载知识库]{path}内容成功加入知识库")
            except Exception as e:
                #exc_info为True会记录详细的报错堆栈，若为false只会记录错误信息
                logger.error(f"[加载知识库]{path}内容失败，错误信息{str(e)}",exc_info=True)
                raise  e
if __name__=="__main__":
    vs=VectorStoreService()
    vs.load_document()
    retriever=vs.get_retriever()
    docs=retriever.invoke("迷雾")
    for f in docs:
        print(f.page_content)
        print(f.metadata)