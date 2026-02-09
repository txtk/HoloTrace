"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-08-20 21:25:01
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-08-20 21:47:39
FilePath: /entity_alignment/src/models/database/neo4j/base.py
Description:节点和关系基类
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

from typing import Literal

from pydantic import BaseModel


def time_parse(raw_dict):
    created_time = raw_dict.get("created")
    modified_time = raw_dict.get("modified")
    if not created_time or not modified_time:
        raise ValueError("Created and modified times must be provided.")
    return {"created_time": created_time, "modified_time": modified_time}



def only_name_parse(name):
    result_dict = {}
    result_dict["name"] = name
    return result_dict


def relation_parse(raw_dict):
    relation_type = raw_dict.get("relationship_type")
    result_dict = time_parse(raw_dict)
    result_dict["relation_type"] = relation_type
    return result_dict


def relation_parse_aadm(raw_dict):
    result_dict = {}
    result_dict["relation_type"] = raw_dict["name"]
    return result_dict

def node_with_description_parse(raw_dict):
    name = raw_dict.get("name")
    description = raw_dict.get("description", "")
    result_dict = time_parse(raw_dict)
    result_dict["name"] = name
    result_dict["description"] = description
    result_dict["semantic"] = 1
    result_dict["importance"] = 0.0
    
    return result_dict


class NodeBase(BaseModel):
    node_type: Literal["node_base"] = "node_base"
    entity_type: str
    unique_id: str
    semantic: int
    importance: float

    class Config:
        from_attributes = True

class NodeWithName(NodeBase):
    node_type: Literal["node_with_name"] = "node_with_name"
    name: str


class NodeBaseWithTime(NodeBase):
    node_type: Literal["node_base_with_time"] = "node_base_with_time"
    created_time: str
    modified_time: str

    class Config:
        from_attributes = True


class Node(NodeBaseWithTime, NodeWithName):
    node_type: Literal["node"] = "node"
    pass

class NodeWithDescription(Node):
    node_type: Literal["node_with_description"] = "node_with_description"
    description: str

    class Config:
        from_attributes = True

class RelationshipBase(BaseModel):
    relation_type: str
    created_time: str
    modified_time: str

    class Config:
        from_attributes = True


class RelationshipBase_AADM(BaseModel):
    relation_type: str

    class Config:
        from_attributes = True
