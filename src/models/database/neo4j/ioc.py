from typing import Literal

from models.database.neo4j.base import NodeWithName
from utils.name_process import get_name, semantic_judge

def ioc_parse(raw_dict):
    name = get_name(raw_dict)
    semantic = semantic_judge(name)
    
    return {"name": name, "semantic": semantic, "importance": 0.0}


class IoC(NodeWithName):
    node_type: Literal["ioc"] = "ioc"
