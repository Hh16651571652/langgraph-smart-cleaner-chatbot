"""yaml格式，k:v格式"""
import yaml
from utils.path_tool import  get_abs_path
def load_rag_config(config_pah:str=get_abs_path("config/rag.yml"),encoding:str="utf-8"):
    with open(config_pah,encoding=encoding) as f:
        # 加载yaml文件,Loader=yaml.FullLoader全量加载
        return yaml.load(f,Loader=yaml.FullLoader)
def load_chroma_config(config_pah:str=get_abs_path("config/chroma.yml"),encoding:str="utf-8"):
    with open(config_pah,encoding=encoding) as f:
        # 加载yaml文件,Loader=yaml.FullLoader全量加载
        return yaml.load(f,Loader=yaml.FullLoader)
def load_prompts_config(config_pah:str=get_abs_path("config/prompts.yml"),encoding:str="utf-8"):
    with open(config_pah,encoding=encoding) as f:
        # 加载yaml文件,Loader=yaml.FullLoader全量加载
        return yaml.load(f,Loader=yaml.FullLoader)
def load_agent_config(config_pah:str=get_abs_path("config/agent.yml"),encoding:str="utf-8"):
    with open(config_pah,encoding=encoding) as f:
        # 加载yaml文件,Loader=yaml.FullLoader全量加载
        return yaml.load(f,Loader=yaml.FullLoader)
rag_conf=load_rag_config()
chroma_conf=load_chroma_config()
prompts_conf=load_prompts_config()
agent_conf=load_agent_config()

if __name__=="__main__":
    print(rag_conf["chat_model_name"])
