from models.database.neo4j.base import NodeWithName
from typing import Literal
from utils.string_operate.regex import Regex

def attack_pattern_parse(raw_dict):
    name = raw_dict.get("name")
    description = raw_dict.get("description", "")
    aliases = raw_dict.get("aliases", [])
    platforms = raw_dict.get("x_mitre_platforms", [])
    x_mitre_description = raw_dict.get("x_mitre_description", "")
    kill_chain_phases = raw_dict.get("kill_chain_phases", [])
    kill_chain_names = []
    phase_names = []
    if not Regex.get_search_judge(r"T\d+", name):
        if len(aliases) > 0:
            name, aliases[0] = aliases[0], name

    for i in kill_chain_phases:
        kill_chain_names.append(i.get("kill_chain_name"))
        phase_names.append(i.get("phase_name"))
    result_dict = {}
    result_dict["name"] = name
    result_dict["description"] = description
    result_dict["aliases"] = aliases
    result_dict["platforms"] = platforms
    result_dict["x_mitre_description"] = x_mitre_description
    result_dict["kill_chain_names"] = kill_chain_names
    result_dict["phase_names"] = phase_names
    result_dict["semantic"] = 1
    result_dict["importance"] = 0.0
    return result_dict


class AttackPattern(NodeWithName):
    node_type: Literal["attack_pattern"] = "attack_pattern"
    description: str
    aliases: list[str]
    platforms: list[str]
    x_mitre_description: str
    kill_chain_names: list[str] = []
    phase_names: list[str] = []
