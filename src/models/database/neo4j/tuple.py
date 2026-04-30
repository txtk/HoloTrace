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
