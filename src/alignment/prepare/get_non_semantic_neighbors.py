from collections import defaultdict

from loguru import logger

from alignment.profile.get_profile import find_neighbours


def prune_missing_endpoint_triplets(attribute_dict, outgoing, incoming, entities):
    valid_ids = set()
    for key in attribute_dict.get_keys():
        try:
            valid_ids.add(int(key))
        except (TypeError, ValueError):
            continue

    cleaned_outgoing = defaultdict(list)
    cleaned_incoming = defaultdict(list)
    cleaned_entities = set()
    removed_triplet_count = 0

    for start_id, triplets in outgoing.items():
        if start_id not in valid_ids:
            removed_triplet_count += len(triplets)
            continue

        for relation_id, end_id in triplets:
            if start_id in valid_ids and end_id in valid_ids:
                cleaned_outgoing[start_id].append((relation_id, end_id))
                cleaned_incoming[end_id].append((relation_id, start_id))
                cleaned_entities.add(start_id)
                cleaned_entities.add(end_id)
            else:
                removed_triplet_count += 1

    logger.info(
        f"[prepare] removed {removed_triplet_count} triplets with missing endpoints before neighbor scanning"
    )
    return cleaned_outgoing, cleaned_incoming, cleaned_entities


def judge_semantic(triplets, target_id):
    no_semantics = []
    none_count = 0
    for triplet in triplets:
        start = triplet["start"]
        end = triplet["end"]
        if start is None or end is None:
            none_count += 1
            continue
        if start["unique_id"] == target_id:
            related_entity = end
        else:
            related_entity = start
        if related_entity.get("semantic") == 0:
            no_semantics.append(related_entity["name"])
    return no_semantics, none_count


def get_non_semantic_neighbors(suffix, attribute_dict, outgoing, incoming, entities):
    total_none_count = 0
    affected_entity_count = 0
    for id, entity in attribute_dict.get_items():
        start_triplets, end_triplets = find_neighbours(id, outgoing, incoming, entities, attribute_dict)
        triplets = start_triplets + end_triplets
        target_id = entity["unique_id"]
        no_semantic_neighbors, none_count = judge_semantic(triplets, target_id)
        if none_count > 0:
            affected_entity_count += 1
            total_none_count += none_count
        entity["no_semantic_neighbors"] = no_semantic_neighbors
    logger.info(
        f"[{suffix}] non-semantic neighbor scan finished: missing-endpoint triplets={total_none_count}, affected entities={affected_entity_count}"
    )


def judge_semantic_icews(triplets, target_id):
    no_semantics = []
    none_count = 0
    for triplet in triplets:
        start = triplet["start"]
        end = triplet["end"]
        if start is None or end is None:
            none_count += 1
            continue
        if start["name"] == target_id:
            related_entity = end
        else:
            related_entity = start
        if related_entity.get("semantic") == 0:
            no_semantics.append(related_entity["name"])
    return no_semantics, none_count


def get_non_semantic_neighbors_icews(attribute_dict, outgoing, incoming, entities):
    total_none_count = 0
    affected_entity_count = 0
    for id, entity in attribute_dict.items():
        start_triplets, end_triplets = find_neighbours(id, outgoing, incoming, entities, attribute_dict)
        triplets = start_triplets + end_triplets
        target_id = entity["name"]
        no_semantic_neighbors, none_count = judge_semantic_icews(triplets, target_id)
        if none_count > 0:
            affected_entity_count += 1
            total_none_count += none_count
            logger.warning(f"[icews] entity {target_id} has {none_count} triplets with missing endpoints")
        entity["no_semantic_neighbors"] = no_semantic_neighbors
    logger.info(
        f"[icews] non-semantic neighbor scan finished: missing-endpoint triplets={total_none_count}, affected entities={affected_entity_count}"
    )
