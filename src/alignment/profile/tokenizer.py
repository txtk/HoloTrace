from os import path

from config import settings
from config.mappings import alignment
from utils.file.json_utils import JsonUtils
from utils.vector.vector_manager import ElasticsearchVectorManager
from models.database.postgre.Neo4jEntityModel import Neo4jEntityModel

async def embedding(vector, query_param):
    vector.index_document(query_param)


async def get_data(entity: dict, dataset_type: str):
    intrusion = await Neo4jEntityModel.aio_get_or_none(id=entity["unique_id"])
    if intrusion is None:
        group_name = entity['name']
    else:
        group_name = intrusion.entity_name
    message = {
        "intrusion_id": entity["unique_id"],
        "content": entity.get("profile"),
        "group": group_name,
        "keyword": entity.get("keywords"),
    }
    return message


async def prepare_data(dataset_type, root_dir):
    if dataset_type == "aadm":
        entity_name = "ThreatActor"
        dataset_col = "aadm_target"
    else:
        entity_name = "intrusion-set"
        dataset_col = "target"
    attribute_path = path.join(root_dir, "target_attributes.json")
    target_attribute_dict = JsonUtils(attribute_path)
    source_target_path = path.join(root_dir, "target_source_labels.json")
    source_target_dict = JsonUtils(source_target_path)
    datas = []
    for _, entity_id in source_target_dict.data.items():
        entity = target_attribute_dict.get_value(str(entity_id[0]))
        result = await get_data(entity, dataset_col)
        datas.append(result)
    return datas


async def tokenizer(mode, root_dir):
    vector = ElasticsearchVectorManager(settings.index_name, alignment)
    vector.recreate_index()
    datas = await prepare_data(mode, root_dir)
    await embedding(vector, datas)
