from .base import NodeWithName
from typing import Literal

def location_parse(raw_dict):
    latitude = raw_dict.get("latitude", 0.0)
    longitude = raw_dict.get("longitude", 0.0)
    name = raw_dict.get("name", "")
    result_dict = {}
    result_dict["name"] = name
    result_dict["latitude"] = latitude
    result_dict["longitude"] = longitude
    result_dict["semantic"] = 1
    result_dict["importance"] = 0.0
    return result_dict

class Location(NodeWithName):
    node_type: Literal["location"] = "location"
    latitude: float
    longitude: float