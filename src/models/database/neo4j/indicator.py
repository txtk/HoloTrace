from .base import NodeWithName, time_parse
from typing import Literal
from utils.name_process import semantic_judge

def indicator_parse(raw_dict):
    name = raw_dict.get("name")
    semantic = semantic_judge(name)
    result_dict = {}
    result_dict["valid_from"] = raw_dict.get("valid_from", "")
    result_dict["valid_until"] = raw_dict.get("valid_until", "")
    result_dict["name"] = name
    result_dict["semantic"] = semantic
    result_dict["importance"] = 0.0
    result_dict["entity_type"] = raw_dict.get("entity_type", "indicator")
    return result_dict

class Indicator(NodeWithName):
    node_type: Literal["indicator"] = "indicator"
    valid_from: str
    valid_until: str