from models.database.neo4j.attackPattern import AttackPattern, attack_pattern_parse
from models.database.neo4j.base import (
    NodeWithName,
    NodeWithDescription,
    RelationshipBase,
    RelationshipBase_AADM,
    relation_parse,
    node_with_description_parse,
    relation_parse_aadm
)
from models.database.neo4j.indicator import Indicator, indicator_parse
from models.database.neo4j.ioc import IoC, ioc_parse
from models.database.neo4j.location import Location, location_parse
from models.database.neo4j.malware import Malware, malware_parse
from models.database.neo4j.report import Report, report_parse
from models.database.neo4j.threaActor import ThreatActor, threat_actor_parse

type_list = [
    "intrusion-set",
    "malware",
    "vulnerability",
    "indicator",
    "report",
    "attack-pattern",
    "relationship",
    "location",
    "tool",
    "domain-name",
    "hostname",
    "file",
    "url",
    "cryptocurrency-wallet",
    "text",
    "email-addr",
    "ipv4-addr",
    "ipv6-addr",
    "windows-registry-key",
    "user-account",
    "email-message",
    "phone-number",
]


type_dict = {
    "relationship": {"class": RelationshipBase, "parse": relation_parse},
    "intrusion-set": {"class": ThreatActor, "parse": threat_actor_parse},
    "tool": {"class": NodeWithDescription, "parse": node_with_description_parse},
    "malware": {"class": Malware, "parse": malware_parse},
    "vulnerability": {"class": NodeWithName, "parse": ioc_parse},
    "indicator": {"class": Indicator, "parse": indicator_parse},
    "report": {"class": Report, "parse": report_parse},
    "attack-pattern": {"class": AttackPattern, "parse": attack_pattern_parse},
    "location": {"class": Location, "parse": location_parse},
    "domain-name": {"class": IoC, "parse": ioc_parse},
    "hostname": {"class": IoC, "parse": ioc_parse},
    "file": {"class": IoC, "parse": ioc_parse},
    "url": {"class": IoC, "parse": ioc_parse},
    "cryptocurrency-wallet": {
        "class": IoC,
        "parse": ioc_parse,
    },  # cryptocurrency-wallet的实体属性和Url相同，所以直接使用url代替
    "text": {"class": IoC, "parse": ioc_parse},
    "email-addr": {"class": IoC, "parse": ioc_parse},
    "ipv4-addr": {"class": IoC, "parse": ioc_parse},
    "ipv6-addr": {"class": IoC, "parse": ioc_parse},
    "windows-registry-key": {"class": IoC, "parse": ioc_parse},
    "user-account": {"class": IoC, "parse": ioc_parse},
    "email-message": {"class": IoC, "parse": ioc_parse},
    "phone-number": {"class": IoC, "parse": ioc_parse},
}


type_list_aadm = [
    "relationship",
    "report",
    "ThreatActor",
    "Malware",
    "Infrastructure",
    "Vulnerability",
    "Identity",
    "Location",
    "AttackPattern",
    "Indicator",
]

type_dict_aadm = {
    "relationship": {"class": RelationshipBase_AADM, "parse": relation_parse_aadm},
    "report": {"class": IoC, "parse": ioc_parse},
    "ThreatActor": {"class": IoC, "parse": ioc_parse},
    "Malware": {"class": IoC, "parse": ioc_parse},
    "Infrastructure": {"class": IoC, "parse": ioc_parse},
    "Vulnerability": {"class": IoC, "parse": ioc_parse},
    "Identity": {"class": IoC, "parse": ioc_parse},
    "Location": {"class": IoC, "parse": ioc_parse},
    "AttackPattern": {"class": IoC, "parse": ioc_parse},
    "Indicator": {"class": IoC, "parse": ioc_parse},
}
