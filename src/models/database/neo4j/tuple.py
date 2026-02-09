"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-08-20 21:33:52
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-08-20 21:47:49
FilePath: /entity_alignment/src/models/database/neo4j/tuple.py
Description:用来存储节点和关系的三元组
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""

from typing import Annotated, Union

from pydantic import BaseModel, Field

from models.database.neo4j.attackPattern import AttackPattern
from models.database.neo4j.base import Node, NodeBaseWithTime, NodeWithName, RelationshipBase, RelationshipBase_AADM, NodeWithDescription
from models.database.neo4j.indicator import Indicator
from models.database.neo4j.ioc import IoC
from models.database.neo4j.location import Location
from models.database.neo4j.malware import Malware
from models.database.neo4j.report import Report
from .threaActor import ThreatActor


class Tuple(BaseModel):
    start: Annotated[
        Union[NodeWithName, AttackPattern, Indicator, Location, Report, IoC, Malware, Node, NodeBaseWithTime, NodeWithDescription, ThreatActor],
        Field(discriminator="node_type"),
    ]
    end: Annotated[
        Union[NodeWithName, AttackPattern, Indicator, Location, Report, IoC, Malware, Node, NodeBaseWithTime, NodeWithDescription, ThreatActor],
        Field(discriminator="node_type"),
    ]
    relation: Union[RelationshipBase, RelationshipBase_AADM]
