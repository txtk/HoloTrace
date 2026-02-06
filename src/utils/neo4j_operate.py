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
    # 2. 执行查询

    records, summary, keys = await driver.execute_query(
        query,
        parameters=parameters,
        database_="neo4j",
    )
    return records


async def insert_pydantic_node(tx: AsyncTransaction, node_object: dict):
    """
    一个通用的异步事务函数，用于在 Neo4j 中创建或更新一个 Pydantic 节点对象。

    Args:
        tx: Neo4j 异步事务对象。
        node_object: 一个继承自 NodeBase 的 Pydantic 对象。
    """
    node_object.pop("node_type")
    label = node_object.get("entity_type")
    unique_id = node_object.get("unique_id")
    # 准备要插入的属性字典
    # 使用 model_dump 排除应用层逻辑字段，如 node_type
    properties = node_object
    # 使用 MERGE 来避免创建重复节点，unique_id 是唯一键
    query = (
        f"MERGE (n:`{label}` {{unique_id: $unique_id}}) "
        "SET n = $props "  # 使用 SET n = $props 来完全同步对象的属性
        "RETURN n.unique_id AS node_id, n.name AS node_name"
    )

    result = await tx.run(query, unique_id=unique_id, props=properties)
    record = await result.single()

    return record.data() if record else None


async def create_or_update_relationship(tx: AsyncTransaction, head_node: dict, tail_node: dict, relationship: dict):
    """
    事务函数：在两个现有节点之间创建或更新关系。

    Args:
        tx: Neo4j 异步事务对象。
        head_node: 关系起始节点的Pydantic对象。
        tail_node: 关系结束节点的Pydantic对象。
        relationship: 关系属性的Pydantic对象。
    """
    head_label = head_node.pop("entity_type")
    tail_label = tail_node.pop("entity_type")
    rel_type = relationship.pop("relation_type")

    # 从Pydantic模型准备关系属性
    rel_props = relationship

    # Cypher查询：
    # 1. MATCH 找到头尾节点
    # 2. MERGE 确保关系唯一性
    # 3. SET 更新关系属性
    query = (
        f"MATCH (head:`{head_label}` {{unique_id: $head_id}}) "
        f"MATCH (tail:`{tail_label}` {{unique_id: $tail_id}}) "
        f"MERGE (head)-[r:`{rel_type}`]->(tail) "
        "SET r = $props "
        "RETURN r.unique_id AS relation_id"
    )

    # logger.info(f"使用参数: head_id={head_node['unique_id']}, tail_id={tail_node['unique_id']}, props={rel_props}")

    result = await tx.run(query, head_id=head_node["unique_id"], tail_id=tail_node["unique_id"], props=rel_props)
    record = await result.single()
    if record is None:
        raise (ValueError("创建或更新关系失败，未返回任何记录。"))


async def get_all_entities_of_type(entity_type, neo4j_type="source"):
    # 1. 修改 Cypher 查询语句
    #    - 使用 size((n)--()) 计算每个节点的总度数（包括出度和入度）
    #    - 使用 AS degree 为度数命名
    #    - 使用 ORDER BY degree DESC 按度数降序排序, ASC 升序
    query = f"""
    MATCH (n:`{entity_type}`)
    RETURN n, COUNT {{ (n)--() }} AS degree
    ORDER BY degree ASC
    """
    records = await excute_query(query, neo4j_type=neo4j_type)
    return records


async def get_all_entities(neo4j_type="source"):
    # 1. 修改 Cypher 查询语句
    #    - 使用 size((n)--()) 计算每个节点的总度数（包括出度和入度）
    #    - 使用 AS degree 为度数命名
    #    - 使用 ORDER BY degree DESC 按度数降序排序, ASC 升序
    query = """
    MATCH (n)
    RETURN n, COUNT { (n)--() } AS degree
    ORDER BY degree ASC
    """
    records = await excute_query(query, neo4j_type=neo4j_type)
    return records


async def delete_all(neo4j_type="source"):
    # 1. 修改 Cypher 查询语句
    #    - 使用 size((n)--()) 计算每个节点的总度数（包括出度和入度）
    #    - 使用 AS degree 为度数命名
    #    - 使用 ORDER BY degree DESC 按度数降序排序, ASC 升序
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
    找出所有存在重复的 unique_id 值。
    假设你的节点属性名为 'unique_id'。如果不是，请修改查询语句中的 'n.unique_id'。
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

        # 将结果转换为列表
        duplicate_ids = [record["unique_id"] async for record in result]
        return duplicate_ids


async def merge_nodes_for_id(unique_id, neo4j_type="source"):
    """
    使用 APOC 合并具有相同 unique_id 的所有节点。
    """
    # 这个查询会找到所有具有给定 unique_id 的节点，
    # 然后调用 apoc.refactor.mergeNodes 将它们合并。
    # 关系会自动转移到合并后的单个节点上。
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
        # 使用 execute_write 来确保事务性
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
            # 将结果转换为列表
            entitys = [record["n"] async for record in result]
            return entitys[0]
        except Exception:
            logger.info(f"未找到 name 为 '{name}' 的实体。")
            return None


async def clean_name_property(neo4j_type="source", label="intrusion-set"):
    """
    对指定标签的节点的name属性进行清洗。
    如果name是列表，则更新为列表的第一个元素。
    """
    driver = get_driver(neo4j_type)

    updated_nodes_count = 0
    skipped_empty_list_count = 0

    # 使用数据库会话执行操作
    async with driver.session() as session:
        # 第一步：获取所有目标节点的 elementId 和 name 属性
        # 使用 elementId() 来获得节点的内部唯一ID，确保更新操作的准确性
        get_nodes_query = f"MATCH (n:`{label}`) RETURN elementId(n) AS id, n.name AS name"

        try:
            results = await session.run(get_nodes_query)
            # 将结果物化为列表，以避免在迭代时操作同一个会话中的资源导致问题
            node_data = [record async for record in results]
        except Exception as e:
            logger.error(f"查询节点时出错: {e}")
            return

        print(f"找到 {len(node_data)} 个 '{label}' 标签的节点，开始处理...")

        # 第二步：在Python中遍历结果并执行条件更新
        for record in node_data:
            node_id = record["id"]
            name_property = record["name"]

            # 判断name属性是否为列表
            if isinstance(name_property, list):
                # 如果列表不为空，则取第一个元素
                if name_property:
                    new_name = name_property[0]

                    # 构建更新查询，使用 elementId 精准定位节点
                    # 使用参数化查询 ($id, $new_name) 来防止Cypher注入，这是最佳安全实践
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
                    # 如果列表为空，则跳过并打印信息
                    print(f"  [跳过] 节点 (ID: {node_id}) 的 name 是一个空列表。")
                    skipped_empty_list_count += 1

            # 如果name是字符串或其他类型，则自动跳过，无需任何操作

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
