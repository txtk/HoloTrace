from alignment.profile.get_profile import find_neighbours
from config import settings
from utils.file.json_utils import JsonUtils
from os import path

def judge_semantic(triplets, target_id):
    no_semantics = []
    for triplet in triplets:
        start = triplet["start"]
        end = triplet["end"]
        if start["unique_id"] == target_id:
            related_entity = end
        else:
            related_entity = start
        if related_entity.get("semantic") == 0:
            no_semantics.append(related_entity["name"])
    return no_semantics

def get_non_semantic_neighbors(suffix, attribute_dict, outgoing, incoming, entities):
    for id, entity in attribute_dict.get_items():
        start_triplets, end_triplets = find_neighbours(id, outgoing, incoming, entities, attribute_dict)
        triplets = start_triplets + end_triplets
        target_id = entity["unique_id"]
        no_semantic_neighbors = judge_semantic(triplets, target_id)
        entity["no_semantic_neighbors"] = no_semantic_neighbors

def judge_semantic_icews(triplets, target_id):
    no_semantics = []
    for triplet in triplets:
        start = triplet["start"]
        end = triplet["end"]
        if start["name"] == target_id:
            related_entity = end
        else:
            related_entity = start
        if related_entity.get("semantic") == 0:
            no_semantics.append(related_entity["name"])
    return no_semantics

def get_non_semantic_neighbors_icews(attribute_dict, outgoing, incoming, entities):
    for id, entity in attribute_dict.items():
        start_triplets, end_triplets = find_neighbours(id, outgoing, incoming, entities, attribute_dict)
        triplets = start_triplets + end_triplets
        target_id = entity["name"]
        no_semantic_neighbors = judge_semantic_icews(triplets, target_id)
        entity["no_semantic_neighbors"] = no_semantic_neighbors