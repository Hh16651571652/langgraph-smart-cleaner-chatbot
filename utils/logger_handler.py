import logging
import os
from datetime import datetime

from .path_tool import get_abs_path
#日志保存的根目录
LOG_ROOT=get_abs_path("logs")
#确保日志的目录存在
os.makedirs(LOG_ROOT,exist_ok=True)
#日志的格式配置
#asctime:创建时间   name：名称  levelname：日志级别 filename文件名 lineno行  message：日志信息
DEFAULT_LOG_FORMAT=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
#console_level:默认级别  file_level:文件级别
def get_logger(name:str="agent",console_level:int=logging.INFO,file_level:int=logging.DEBUG,log_file=None):
    #创建日志管理器
    logger=logging.getLogger(name)
    #设置日志级别
    logger.setLevel(logging.DEBUG)
    #避免重复添加Handler:
    if logger.handlers:
        return logger
    #创建（控制台显示）
    #创建控制Handler
    console_handler=logging.StreamHandler()
    #设置控制Handler级别
    console_handler.setLevel(console_level)
    #设置控制Handler格式
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    #添加控制Handler（到日志管理器中）
    logger.addHandler(console_handler)
    #文件Handler（文件中的日志记录）
    if log_file is None:
        log_file=os.path.join(LOG_ROOT,f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    #创建文件Handler
    file_handler=logging.FileHandler(log_file,encoding="utf-8")
    #设置文件Handler级别
    file_handler.setLevel(file_level)
    #设置文件Handler格式
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    #将文件Handler添加到日志管理器中
    logger.addHandler(file_handler)
    #返回日志管理器
    return logger
#快捷获取日志器
logger=get_logger()
if __name__=="__main__":
    logger.debug("调试日志")
    logger.info("信息日志")
    logger.warning("警告日志")
    logger.error("错误日志")
    logger.critical("critical")