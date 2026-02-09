from .base import node_with_description_parse, NodeWithDescription
from typing import Literal

def threat_actor_parse(raw_dict):
    name = raw_dict.get("group_name")
    result = node_with_description_parse(raw_dict)
    result["group_name"] = name
    return result

class ThreatActor(NodeWithDescription):
    node_type: Literal["threat_actor"] = "threat_actor"
    group_name: str
    aka_name: list[str] = []

    class Config:
        from_attributes = True