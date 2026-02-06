from typing import Any, Dict, Optional
from uuid import NAMESPACE_DNS, uuid5

from elasticsearch import helpers
from elasticsearch.helpers import BulkIndexError
from loguru import logger

from config import elastic

from .query_builders import KNNQueryBuilder, TermsQueryBuilder
from .RRF import RRF


class ElasticsearchVectorManager:
    def __init__(self, index_name: str, mappings: dict, vector_dimensions: int = 1024, num_results: int = 10):
        """
        初始化 ElasticsearchVectorManager。

        :param index_name: 要操作的 Elasticsearch 索引名称。
        :param openai_embedding_model: 用于生成向量的 OpenAI 模型名称。
        :param vector_dimensions: 向量的维度，必须与所选模型匹配。
        """
        self.index_name = index_name
        self.vector_dimensions = vector_dimensions
        self.num_results = num_results

        self.es_client = elastic  # 使用全局的 Elasticsearch 客户端实例
        self.mappings = mappings
        # 检查连接
        if not self.es_client.ping():
            raise ConnectionError("无法连接到 Elasticsearch！请检查配置。")

    def get_insert_action(self, docs: list):
        actions = []
        for doc in docs:
            # 优先使用文档中显式指定的 _id
            doc_id = doc.get("_id")

            if not doc_id:
                # 使用 name (小写化) 和 raw_content 作为唯一标识生成 ID，提高大小写鲁棒性
                name_for_id = str(doc.get("name", "")).lower()
                identifier = f"{name_for_id}_{doc.get('raw_content', '')}"
                doc_id = str(uuid5(NAMESPACE_DNS, identifier))

            # 准备 source 数据，如果文档中有 _id，我们不把它存入 _source 内部
            source = doc.copy()
            if "_id" in source:
                del source["_id"]

            actions.append(
                {
                    "_id": doc_id,
                    "_index": self.index_name,
                    "_op_type": "index",  # 使用 index，如果 ID 重复则覆盖更新
                    "_source": source,
                }
            )
        return actions

    def index_document(self, docs: list) -> Dict[str, Any]:
        actions = self.get_insert_action(docs)
        try:
            # 执行 bulk 插入
            success, failed = helpers.bulk(self.es_client, actions)
            logger.info(f"Successfully indexed {success} documents.")
            if failed:
                logger.info(f"Failed to index {len(failed)} documents.")
        except BulkIndexError as e:
            for i, error_info in enumerate(e.errors[:5]):
                logger.info(f"\n--- 错误 {i + 1} ---")
                # 错误信息通常在 'index', 'create', 或 'update' 键下
                action, result = next(iter(error_info.items()))
                logger.info(f"操作类型: {action}")
                logger.info(f"文档ID (_id): {result.get('_id')}")
                logger.info(f"索引 (_index): {result.get('_index')}")
                logger.info(f"失败原因 (reason): {result.get('error', {}).get('reason')}")
                logger.info(f"失败类型 (type): {result.get('error', {}).get('type')}")
                # 有时更深层的原因在这里
                if "caused_by" in result.get("error", {}):
                    logger.info(f"根本原因 (caused_by): {result['error']['caused_by']}")

    def build_query_hybrid(self, retrievers):
        rrf = RRF()
        rrf.add_retrievers(retrievers)
        return rrf.get_query()

    def build_query_terms(self, field: str, values: list):
        builder = TermsQueryBuilder(field, values)
        return builder.get_query()

    def build_query_knn(self, vector_field: str, query_vector: list, k: int = 10, num_candidates: int = 100):
        builder = KNNQueryBuilder(vector_field, query_vector, k, num_candidates)
        return builder.get_query()

    def perform_search(self, query, top_k=None):
        if top_k is None:
            top_k = self.num_results
        response = self.es_client.search(
            index=self.index_name,
            body=query,
            size=top_k,  # 获取足够多的结果以供后续重排
        )
        return response["hits"]["hits"]

    def perform_search_detailed(self, query, top_k=None):
        """
        执行查询并返回包含详细信息（如相似度分数、命中总数）的结果。
        :return: (results, total_hits)
        """
        if top_k is None:
            top_k = self.num_results
        response = self.es_client.search(
            index=self.index_name,
            body=query,
            size=top_k,
        )
        hits = response["hits"]["hits"]
        total_hits = response["hits"]["total"]["value"]

        results = []
        for hit in hits:
            source = hit["_source"]
            source["_id"] = hit["_id"]
            # _score 在基于向量的查询中即代表相似度
            source["_score"] = hit["_score"]
            results.append(source)

        return results, total_hits

    def get_index_mapping(self):
        """
        获取指定索引的 Mapping 信息。
        """
        # 使用 indices.get_mapping 方法
        mapping = self.es_client.indices.get_mapping(index=self.index_name)
        mapping = mapping.get(self.index_name)
        return mapping["mappings"]

    def index_exists(self, index_name: Optional[str] = None) -> bool:
        """
        检查指定索引是否存在。

        :param index_name: 要检查的索引名，若为 None 则使用实例的 `self.index_name`。
        :return: 存在返回 True，否则 False（包括发生异常时返回 False 并记录日志）。
        """
        idx = index_name or self.index_name
        try:
            return self.es_client.indices.exists(index=idx)
        except Exception as e:
            logger.exception(f"检查索引存在性时出错: {idx} - {e}")
            return False

    def delete_index(self):
        """
        删除指定的索引。
        """
        # 使用 indices.delete 方法
        # ignore_unavailable=True 表示如果索引不存在，也不会报错
        response = self.es_client.indices.delete(index=self.index_name, ignore_unavailable=True)
        if response.get("acknowledged"):
            return True
        else:
            # 这种情况在 ignore_unavailable=True 时通常不会发生，除非权限问题等
            return False

    def create_index(self, settings: dict = None):
        """
        创建一个新的索引，并可以指定 Mappings 和 Settings。
        """
        # 首先检查索引是否已存在
        if self.es_client.indices.exists(index=self.index_name):
            logger.info(f"索引 '{self.index_name}' 已经存在，无需创建。")
            return False

        # 使用 indices.create 方法创建索引
        # Mappings 和 Settings 作为参数传入
        response = self.es_client.indices.create(index=self.index_name, mappings=self.mappings, settings=settings)

        if response.get("acknowledged"):
            logger.info(f"索引 '{self.index_name}' 创建成功。")
            return True
        else:
            logger.info(f"索引 '{self.index_name}' 创建失败。")
            return False

    def recreate_index(self, settings: dict = None):
        """
        重新创建索引：如果索引已存在则删除，然后创建一个新的索引。
        """
        # 删除已存在的索引
        self.delete_index()
        # 创建新的索引
        return self.create_index(settings)

    def count_documents(self) -> int:
        """
        统计索引中的文档数量。
        """
        try:
            response = self.es_client.count(index=self.index_name)
            return response["count"]
        except Exception as e:
            logger.error(f"统计索引文档数量时出错: {self.index_name} - {e}")
            return 0
