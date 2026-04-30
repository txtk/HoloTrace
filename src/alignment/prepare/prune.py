from os import path

from config import settings
from utils.file.json_utils import JsonUtils
from utils.neo4j_pruner import Neo4jPruner


async def prune(neo4j_type):
    pruner = Neo4jPruner(neo4j_type)
    layer_path = path.join(settings.json_dir, "layer.json")
    layer = JsonUtils(layer_path)

    high_list = layer.get_value("layer3") + layer.get_value("layer4") + [layer.get_value("layer2")[1]]
    low_level = layer.get_value("layer1")
    for low in low_level:
        for high in high_list:
            await pruner.execute_pruning(high, low, "indicator")
