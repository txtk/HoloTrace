from typing import Any, Dict, List

from loguru import logger
from neo4j import AsyncTransaction

from config import neo4j_driver, neo4j_driver_sub


def get_driver(neo4j_type):
    if neo4j_type == "source":
        driver = neo4j_driver
    else:
        driver = neo4j_driver_sub
    return driver


async def excute_query(query, parameters=None, neo4j_type="source"):
    driver = get_driver(neo4j_type)
    # 2. Execute query

    records, summary, keys = await driver.execute_query(
        query,
        parameters=parameters,
        database_="neo4j",
    )
    return records


async def insert_pydantic_node(tx: AsyncTransaction, node_object: dict):
    """
    A generic async transaction function for creating or updating a Pydantic node object in Neo4j.

    Args:
        tx: Neo4j async transaction object.
        node_object: a Pydantic object that inherits from NodeBase.
    """
    node_object.pop("node_type")
    label = node_object.get("entity_type")
    unique_id = node_object.get("unique_id")
    # Prepare the property dictionary to insert
    # Use model_dump to exclude application-layer logic fields such as node_type
    properties = node_object
    # Use MERGE to avoid creating duplicate nodes; unique_id is the unique key
    query = (
        f"MERGE (n:`{label}` {{unique_id: $unique_id}}) "
        "SET n = $props "  # Use SET n = $props to fully synchronize object properties
        "RETURN n.unique_id AS node_id, n.name AS node_name"
    )

    result = await tx.run(query, unique_id=unique_id, props=properties)
    record = await result.single()

    return record.data() if record else None


async def create_or_update_relationship(tx: AsyncTransaction, head_node: dict, tail_node: dict, relationship: dict):
    """
    Transaction function: create or update a relationship between two existing nodes.

    Args:
        tx: Neo4j async transaction object.
        head_node: Pydantic object for the relationship start node.
        tail_node: Pydantic object for the relationship end node.
        relationship: Pydantic object for relationship properties.
    """
    head_label = head_node.pop("entity_type")
    tail_label = tail_node.pop("entity_type")
    rel_type = relationship.pop("relation_type")

    # Prepare relationship properties from the Pydantic model
    rel_props = relationship

    # Cypher query:
    # 1. MATCH finds the head and tail nodes
    # 2. MERGE ensures relationship uniqueness
    # 3. SET updates relationship properties
    query = (
        f"MATCH (head:`{head_label}` {{unique_id: $head_id}}) "
        f"MATCH (tail:`{tail_label}` {{unique_id: $tail_id}}) "
        f"MERGE (head)-[r:`{rel_type}`]->(tail) "
        "SET r = $props "
        "RETURN r.unique_id AS relation_id"
    )

    # logger.info(f"Use parameters: head_id={head_node['unique_id']}, tail_id={tail_node['unique_id']}, props={rel_props}")

    result = await tx.run(query, head_id=head_node["unique_id"], tail_id=tail_node["unique_id"], props=rel_props)
    record = await result.single()
    if record is None:
        raise (ValueError("创建或更新关系失败，未返回任何记录。"))


async def get_all_entities_of_type(entity_type, neo4j_type="source"):
    # 1. Modify the Cypher query
    #    - Use size((n)--()) to calculate each node's total degree, including outgoing and incoming degree
    #    - Use AS degree to name the degree value
    #    - Use ORDER BY degree DESC for descending degree order, ASC for ascending order
    query = f"""
    MATCH (n:`{entity_type}`)
    RETURN n, COUNT {{ (n)--() }} AS degree
    ORDER BY degree ASC
    """
    records = await excute_query(query, neo4j_type=neo4j_type)
    return records


async def get_all_entities(neo4j_type="source"):
    # 1. Modify the Cypher query
    #    - Use size((n)--()) to calculate each node's total degree, including outgoing and incoming degree
    #    - Use AS degree to name the degree value
    #    - Use ORDER BY degree DESC for descending degree order, ASC for ascending order
    query = """
    MATCH (n)
    RETURN n, COUNT { (n)--() } AS degree
    ORDER BY degree ASC
    """
    records = await excute_query(query, neo4j_type=neo4j_type)
    return records


async def delete_all(neo4j_type="source"):
    # 1. Modify the Cypher query
    #    - Use size((n)--()) to calculate each node's total degree, including outgoing and incoming degree
    #    - Use AS degree to name the degree value
    #    - Use ORDER BY degree DESC for descending degree order, ASC for ascending order
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    records = await excute_query(query, neo4j_type=neo4j_type)
    return records


async def get_entity_surround(entity_type: str, unique_id: str, neo4j_type: str = "source") -> List[Dict[str, Any]]:
    async def _get_entity_surround(triplets, query, neo4j_type):
        driver = get_driver(neo4j_type)
        result = await driver.execute_query(query, {"unique_id": unique_id})
        if len(result.records) < 1:
            return []
        for record in result.records:
            start_entity = {}
            start_entity[record["start_labels"][0]] = record["start_entity"]
            end_entity = {}
            end_entity[record["end_labels"][0]] = record["end_entity"]
            relation = {}
            relation[record["relationship_type"]] = record["relationship_properties"]
            triplet = {
                "start": start_entity,
                "end": end_entity,
                "relation": relation,
            }
            triplets.append(triplet)
        return triplets

    query_start = f"""
    MATCH (e:`{entity_type}` {{unique_id: $unique_id}})-[r]->(other)
    RETURN 
        e AS start_entity,
        TYPE(r) AS relationship_type,
        properties(r) AS relationship_properties,
        other AS end_entity,
        labels(other) AS end_labels,
        labels(e) AS start_labels
    """
    query_end = f"""
    MATCH (other)-[r]->(e:`{entity_type}` {{unique_id: $unique_id}})
    RETURN 
        other AS start_entity,
        TYPE(r) AS relationship_type,
        properties(r) AS relationship_properties,
        e AS end_entity,
        labels(other) AS start_labels,
        labels(e) AS end_labels
    """

    start_triplets = []
    start_triplets = await _get_entity_surround(start_triplets, query_start, neo4j_type)
    end_triplets = []
    end_triplets = await _get_entity_surround(end_triplets, query_end, neo4j_type)

    return start_triplets, end_triplets


async def get_entity_by_id(entity_type, unique_id, neo4j_type="source"):
    query = f"MATCH (n:`{entity_type}`) WHERE n.unique_id = $unique_id RETURN n"
    driver = get_driver(neo4j_type)
    async with driver.session() as session:
        result = await session.run(query, unique_id=unique_id)
        records = [record["n"] async for record in result]
    return records[0]


async def insert_profile(entity_type, unique_id, profile, neo4j_type="source"):
    query = (
        f"MATCH (n:`{entity_type}` {{unique_id: $unique_id}}) "
        "SET n.profile = $profile "
        "RETURN n.unique_id AS id, n.profile AS profile"
    )
    properties = {"unique_id": unique_id, "profile": profile}
    return await insert_properties(query, properties, neo4j_type)

async def insert_keywords(entity_type, unique_id, keywords, neo4j_type="source"):
    query = (
        f"MATCH (n:`{entity_type}` {{unique_id: $unique_id}}) "
        "SET n.keywords = $keywords "
        "RETURN n.unique_id AS id, n.keywords AS keywords"
    )
    properties = {"unique_id": unique_id, "keywords": keywords}
    return await insert_properties(query, properties, neo4j_type)


async def insert_semantic(unique_id, semantic, neo4j_type="source"):
    query = (
        "MATCH (n) "
        "WHERE n.unique_id = $unique_id "
        "SET n.semantic = $semantic "
        "RETURN n.unique_id AS id, n.semantic AS semantic"
    )
    properties = {"unique_id": unique_id, "semantic": semantic}
    return await insert_properties(query, properties, neo4j_type)


async def insert_nf_ipf(unique_id, nfipf, neo4j_type="source"):
    query = "MATCH (n) WHERE n.unique_id = $unique_id SET n.nfipf = $nfipf RETURN n.unique_id AS id, n.nfipf AS nfipf"
    properties = {"unique_id": unique_id, "nfipf": nfipf}
    return await insert_properties(query, properties, neo4j_type)


async def insert_properties(query, properties, neo4j_type="source"):
    driver = get_driver(neo4j_type)
    async with driver.session() as session:
        result = await session.run(query, properties)
    summary = await result.consume()
    if summary.counters.properties_set > 0:
        print(f"成功！更新了 {summary.counters.properties_set} 个属性。")
        return True


async def find_duplicate_ids(neo4j_type):
    """
    Find all duplicate unique_id values.
    Assume the node property is named 'unique_id'. If not, update 'n.unique_id' in the query.
    """
    query = """
    MATCH (n)
    WHERE n.unique_id IS NOT NULL
    WITH n.unique_id AS unique_id, collect(n) AS nodes
    WHERE size(nodes) > 1
    RETURN unique_id
    """
    driver = get_driver(neo4j_type)
    async with driver.session() as session:
        result = await session.run(query)

        # Convert results to a list
        duplicate_ids = [record["unique_id"] async for record in result]
        return duplicate_ids


async def merge_nodes_for_id(unique_id, neo4j_type="source"):
    """
    Use APOC to merge all nodes with the same unique_id.
    """
    # This query finds all nodes with the given unique_id,
    # then calls apoc.refactor.mergeNodes to merge them.
    # Relationships are automatically moved to the merged single node.
    query = """
    MATCH (n {unique_id: $unique_id})
    WITH collect(n) AS nodes
    WHERE size(nodes) > 0
    CALL apoc.refactor.mergeNodes(nodes, {
        properties: 'combine', 
        mergeRels: true
    })
    YIELD node
    RETURN node
    """
    driver = get_driver(neo4j_type)
    async with driver.session() as session:
        # Use execute_write to ensure transactionality
        result = await session.run(query, unique_id=unique_id)
        try:
            record = await result.single()
        except Exception as e:
            logger.error(f"合并 unique_id '{unique_id}' 时出错: {e}")


async def get_intrusion_by_name(name, neo4j_type="source"):
    query = """
    MATCH (n:`intrusion-set`)
    WHERE n.name = $name
    RETURN n
    """
    driver = get_driver(neo4j_type)
    async with driver.session() as session:
        result = await session.run(query, name=name)
        try:
            # Convert results to a list
            entitys = [record["n"] async for record in result]
            return entitys[0]
        except Exception:
            logger.info(f"未找到 name 为 '{name}' 的实体。")
            return None


async def clean_name_property(neo4j_type="source", label="intrusion-set"):
    """
    Clean the name property for nodes with the specified label.
    If name is a list, update it to the first element of the list.
    """
    driver = get_driver(neo4j_type)

    updated_nodes_count = 0
    skipped_empty_list_count = 0

    # Use the database session to execute operations
    async with driver.session() as session:
        # Step 1: get elementId and name properties for all target nodes
        # Use elementId() to get the node's internal unique ID and ensure accurate updates
        get_nodes_query = f"MATCH (n:`{label}`) RETURN elementId(n) AS id, n.name AS name"

        try:
            results = await session.run(get_nodes_query)
            # Materialize results as a list to avoid issues from operating on the same session resources while iterating
            node_data = [record async for record in results]
        except Exception as e:
            logger.error(f"查询节点时出错: {e}")
            return

        print(f"找到 {len(node_data)} 个 '{label}' 标签的节点，开始处理...")

        # Step 2: iterate through results in Python and conditionally update them
        for record in node_data:
            node_id = record["id"]
            name_property = record["name"]

            # Check whether the name property is a list
            if isinstance(name_property, list):
                # If the list is not empty, take its first element
                if name_property:
                    new_name = name_property[0]

                    # Build the update query and use elementId to precisely locate the node
                    # Use parameterized queries ($id, $new_name) to prevent Cypher injection, which is a security best practice
                    update_query = """
                    MATCH (n)
                    WHERE elementId(n) = $id
                    SET n.name = $new_name
                    """
                    try:
                        await session.run(update_query, id=node_id, new_name=new_name)
                        updated_nodes_count += 1
                    except Exception as e:
                        logger.error(f"更新节点 (ID: {node_id}) 时出错: {e}")

                else:
                    # If the list is empty, skip it and print a message
                    print(f"  [跳过] 节点 (ID: {node_id}) 的 name 是一个空列表。")
                    skipped_empty_list_count += 1

            # If name is a string or another type, skip it without any action

    print("\n--- 处理完成 ---")
    print(f"总共更新了 {updated_nodes_count} 个节点。")
    if skipped_empty_list_count > 0:
        print(f"跳过了 {skipped_empty_list_count} 个 name 为空列表的节点。")


def entity_compose(entity, label):
    result = {
        "entity_id": entity.element_id,
        "entity_type": label,
        "properties": entity._properties,
    }
    return result


async def get_all(neo4j_type: str = "source") -> List[Dict[str, Any]]:
    async def _get_entity_surround(triplets, query, neo4j_type):
        driver = get_driver(neo4j_type)
        result = await driver.execute_query(query)
        if len(result.records) < 1:
            return []
        for record in result.records:
            start_entity = record["start"]
            end_entity = record["end"]
            start_label = record["start_labels"][0]
            end_label = record["end_labels"][0]
            relation = record["r"]
            relation_type = record["relationship_type"]
            relation_properties = record["relationship_properties"]
            start = entity_compose(start_entity, start_label)
            end = entity_compose(end_entity, end_label)
            relation = {
                "relation_id": relation.element_id,
                "relation_type": relation_type,
                "properties": relation_properties,
                "start_id": start["entity_id"],
                "end_id": end["entity_id"],
            }

            triplet = {
                "start": start,
                "end": end,
                "relation": relation,
            }
            triplets.append(triplet)
        return triplets

    query = """
    MATCH (start)-[r]->(end)
    RETURN 
        start,
        TYPE(r) AS relationship_type,
        properties(r) AS relationship_properties,
        r,
        end,
        labels(end) AS end_labels,
        labels(start) AS start_labels
    """
    triplets = []
    triplets = await _get_entity_surround(triplets, query, neo4j_type)

    return triplets
