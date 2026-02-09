import poml
from elasticsearch import Elasticsearch
from neo4j import AsyncGraphDatabase

from config.config import get_settings
from utils.database.db import get_db_instance
from OTXv2 import OTXv2


settings = get_settings()


db_config = {
    "host": settings.postgres_host,
    "port": settings.postgres_port,
    "user": settings.postgres_user,
    "password": settings.postgres_password,
    "database": settings.postgres_db,
    "max_connections": settings.max_connection,
}


# Neo4j配置
neo4j_config = {
    "uri": settings.neo4j_uri,
    "user": settings.neo4j_user,
    "password": settings.neo4j_password,
}

# Neo4j临时图配置
neo4j_config_sub = {
    "uri": settings.neo4j_sub_uri,
    "user": settings.neo4j_user,
    "password": settings.neo4j_password,
}

db = get_db_instance(db_config)

neo4j_driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
neo4j_driver_sub = AsyncGraphDatabase.driver(
    settings.neo4j_sub_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)

elastic = Elasticsearch(settings.elastic_url, api_key=settings.elastic_api, request_timeout=30)
# neo4j_sub = get_neo4j_instance(neo4j_config_sub)

# asyncio.run(get_connection(neo4j_sub))
poml.set_trace(False, trace_dir=settings.poml_log_dir)


profile_mode = [
    # (True, False, True, True, 0, "profile_without_enhance_0"),
    # (True, False, True, False, 0, "profile_without_enhance_0_no_hsage"),
    # (True, False, True, True, 20, "profile_without_enhance_20"),
    # (True, False, True, False, 20, "profile_without_enhance_20_no_hsage"),
    # (True, False, True, False, 15, "profile_without_enhance_15_no_hsage"),
    # (True, False, True, True, 15, "profile_without_enhance_15"),
    # (True, False, True, True, 10, "profile_without_enhance"),
    # (True, False, True, False, 10, "profile_without_enhance_10_no_hsage"),
    # (False, False, True, True, 5, "profile_without_enhance_5_without_profile"),
    # (True, False, False, True, 5, "profile_without_enhance_5_without_retriver"),
    # (False, False, False, True, 5, "profile_without_enhance_5_without_profile_retriver"),
    (True, False, True, True, 5, "profile_without_enhance_5"),
    # (True, False, True, False, 5, "profile_without_enhance_5_no_hsage"),
    # (True, False, True, True, 1, "profile_without_enhance_1"),
    # (True, False, True, False, 1, "profile_without_enhance_1_no_hsage"),
    
]


profile_mode_aadm = [
    # (True, False, True, True, 5, "profile_without_enhance_5"),
    # (True, False, True, False, 5, "profile_without_enhance_5_no_hsage"),
    # (True, False, True, True, 0, "profile_without_enhance_0"),
    # (True, False, True, False, 0, "profile_without_enhance_0_no_hsage"),
    # (True, False, True, True, 20, "profile_without_enhance_20"),
    # (True, False, True, False, 20, "profile_without_enhance_20_no_hsage"),
    # (True, False, True, False, 15, "profile_without_enhance_15_no_hsage"),
    # (True, False, True, True, 15, "profile_without_enhance_15"),
    (True, False, True, True, 10, "profile_without_enhance"),
    # (True, False, True, False, 10, "profile_without_enhance_10_no_hsage"),
    # (True, False, True, True, 1, "profile_without_enhance_1"),
    # (True, False, True, False, 1, "profile_without_enhance_1_no_hsage"),    
]

match_mode_test = [
    (True, True, "profile"),
    (True, True, "profile_without_neighbour"),
    (True, True, "profile_without_enhance"),
    (True, True, "profile_without_retriver"),
]

match_mode_mine = [
    # (True, True, "profile_without_enhance_20", 10),
    # (True, True, "profile_without_enhance_20_no_hsage", 10),
    # (True, True, "profile_without_enhance_15", 10),
    # (True, True, "profile_without_enhance_15_no_hsage", 10),
    # (True, True, "profile_without_enhance", 10),
    # (True, True, "profile_without_enhance_10_no_hsage", 10),
    # (True, True, "profile_without_enhance_5", 10),
    # (True, True, "profile_without_enhance_5_no_hsage", 10),
    # (True, True, "profile_without_enhance_1", 10),
    # (True, True, "profile_without_enhance_1_no_hsage", 10),
    # (True, True, "profile_without_enhance_0", 10),
    # (True, True, "profile_without_enhance_0_no_hsage", 10),


    (True, True, "profile_without_enhance_5", 10),
    # (True, True, "profile_without_enhance_5_without_profile", 10),
    # (True, True, "profile_without_enhance_5_without_retriver", 10),
    # (False, True, "profile_without_enhance_5", 10),
    # (True, False, "profile_without_enhance_5", 10),
    # (False, False, "profile_without_enhance_5", 10),
    # (False, False, "profile_without_enhance_5_without_retriver", 10),
    # (False, False, "profile_without_enhance_5_without_profile_retriver", 10),
]
match_mode_aadm = [
    # (True, True, "profile_without_enhance_20", 10),
    # (True, True, "profile_without_enhance_20_no_hsage", 10),
    # (True, True, "profile_without_enhance_15", 10),
    # (True, True, "profile_without_enhance_15_no_hsage", 10),
    (True, True, "profile_without_enhance", 10),
    # (True, True, "profile_without_enhance_10_no_hsage", 10),
    # (True, True, "profile_without_enhance_5", 10),
    # (True, True, "profile_without_enhance_5_no_hsage", 10),
    # (True, True, "profile_without_enhance_1", 10),
    # (True, True, "profile_without_enhance_1_no_hsage", 10),
    # (True, True, "profile_without_enhance_0", 10),
    # (True, True, "profile_without_enhance_0_no_hsage", 10),
]

aadm_ignore_properties = [
    "no_semantic_neighbors",
    "unique_id",
    "processed",
    "semantic",
    "hsage",
    "profile",
    "profile_without_enhance",
    "profile_without_neighbour",
    "profile_without_retriver",
    "profile_without_enhance_15",
    "profile_without_enhance_15_no_hsage",
    "profile_without_enhance_20",
    "profile_without_enhance_20_no_hsage",
    "profile_without_enhance",
    "profile_without_enhance_10_no_hsage",
    "profile_without_enhance_5",
    "profile_without_enhance_5_no_hsage",
    "profile_without_enhance_1",
    "profile_without_enhance_1_no_hsage",
    "profile_without_enhance_0",
    "profile_without_enhance_0_no_hsage",
    "profile_without_enhance_5_without_profile",
    "profile_without_enhance_5_without_retriver",
    "profile_without_enhance_5_without_profile_retriver"
]

mine_ignore_properties = [
    "no_semantic_neighbors",
    "unique_id",
    "processed",
    "valid_until",
    "label_description",
    "created_time",
    "nf_ipf",
    "x_mitre_description",
    "latitude",
    "semantic",
    "description",
    "standard_attck_name",
    "standard_attck_id",
    "hsage",
    "gid",
    "longitude",
    "group_name",
    "modified_time",
    "valid_from",
    "profile",
    "profile_without_enhance",
    "profile_without_neighbour",
    "profile_without_retriver",
    "profile_without_enhance_15",
    "profile_without_enhance_15_no_hsage",
    "profile_without_enhance_20",
    "profile_without_enhance_20_no_hsage",
    "profile_without_enhance",
    "profile_without_enhance_10_no_hsage",
    "profile_without_enhance_5",
    "profile_without_enhance_5_no_hsage",
    "profile_without_enhance_1",
    "profile_without_enhance_1_no_hsage",
    "profile_without_enhance_0",
    "profile_without_enhance_0_no_hsage",
    "profile_without_enhance_5_without_profile",
    "profile_without_enhance_5_without_retriver",
    "profile_without_enhance_5_without_profile_retriver"
]

ignore_dict = {
    "aadm": aadm_ignore_properties,
    "mine": mine_ignore_properties,
}


otx_clients = [OTXv2(api_key=key) for key in settings.alienvault_apikey]