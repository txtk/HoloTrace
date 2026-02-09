"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-08-21 10:53:11
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-08-21 11:28:47
FilePath: /entity_alignment/src/models/database/neo4j/attackPattern.py
Description:攻击模式
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

from models.database.neo4j.base import Node, time_parse
from typing import Literal


def report_parse(raw_dict):
    description = raw_dict.get("description", "")
    external_references = raw_dict.get("external_references", [])
    result_dict = time_parse(raw_dict)
    result_dict["name"] = raw_dict.get("name")
    result_dict["description"] = description
    result_dict["external_references"] = external_references
    result_dict["semantic"] = 1
    result_dict["importance"] = 0.0
    return result_dict


class Report(Node):
    node_type: Literal["report"] = "report"
    description: str
    external_references: list[dict]
