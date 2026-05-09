import os
from utils.logger_handler import logger
import hashlib
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader,TextLoader
def get_md5_hex(filepath:str):#获取文件的md5的十六进制字符串
    if not os.path.exists(filepath):
        logger.error(f"[md计算]文件{filepath}不存在")
        return
    if not os.path.isfile(filepath):
        logger.error(f"[md计算]路径{filepath}不是文件")
        return
    #获取md对象
    md5_obj=hashlib.md5()
    chunk_size=4096 #4KB分片，避免文件过大爆内存
    try:
        with open(filepath,"rb") as f:#分片，必须二进制
            while chunk:=f.read(chunk_size):#:=是赋值运算符，它是先将右边的表达式赋值给左边的变量再进行while判断
                md5_obj.update(chunk)
            md5_hex=md5_obj.hexdigest()#获取最终的md5字符串
            return md5_hex
    except Exception as e:
        logger.error(f"[md计算]文件{filepath}计算md5失败，错误信息{e}")
        return None

def listdir_with_allowed_type(path:str,allowed_types:tuple[str]):#返回文件夹内的文件列表（允许的文件后缀）
     files=[]
     if not os.path.isdir(path):
         logger.error(f"[listdir_with_allowed_type]路径{path}不是文件夹")
         return files
     for f in os.listdir(path):
         if f.endswith(allowed_types):
             files.append(os.path.join(path,f))
     return tuple(files)
def pdf_loader(filepath:str,password=None):
    return PyPDFLoader(filepath,password=password).load()
def txt_loader(filepath:str):
     return TextLoader(filepath, encoding="utf-8").load()
