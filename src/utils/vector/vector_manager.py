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
        Initialize ElasticsearchVectorManager.

        :param index_name: Name of the Elasticsearch index to operate on.
        :param openai_embedding_model: OpenAI model name used to generate vectors.
        :param vector_dimensions: Vector dimensions; must match the selected model.
        """
        self.index_name = index_name
        self.vector_dimensions = vector_dimensions
        self.num_results = num_results

        self.es_client = elastic  # Use the global Elasticsearch client instance
        self.mappings = mappings
        # Check the connection
        if not self.es_client.ping():
            raise ConnectionError("无法连接到 Elasticsearch！请检查配置。")

    def get_insert_action(self, docs: list):
        actions = []
        for doc in docs:
            # Prefer the _id explicitly specified in the document
            doc_id = doc.get("_id")

            if not doc_id:
                # Use lowercased name and raw_content as the unique identifier for ID generation to improve case robustness
                name_for_id = str(doc.get("name", "")).lower()
                identifier = f"{name_for_id}_{doc.get('raw_content', '')}"
                doc_id = str(uuid5(NAMESPACE_DNS, identifier))

            # Prepare source data; if the document has _id, do not store it inside _source
            source = doc.copy()
            if "_id" in source:
                del source["_id"]

            actions.append(
                {
                    "_id": doc_id,
                    "_index": self.index_name,
                    "_op_type": "index",  # Use index; if the ID is duplicated, overwrite and update
                    "_source": source,
                }
            )
        return actions

    def index_document(self, docs: list) -> Dict[str, Any]:
        actions = self.get_insert_action(docs)
        try:
            # Execute bulk insert
            success, failed = helpers.bulk(self.es_client, actions)
            logger.info(f"Successfully indexed {success} documents.")
            if failed:
                logger.info(f"Failed to index {len(failed)} documents.")
        except BulkIndexError as e:
            for i, error_info in enumerate(e.errors[:5]):
                logger.info(f"\n--- 错误 {i + 1} ---")
                # Error details are usually under the 'index', 'create', or 'update' key
                action, result = next(iter(error_info.items()))
                logger.info(f"操作类型: {action}")
                logger.info(f"文档ID (_id): {result.get('_id')}")
                logger.info(f"索引 (_index): {result.get('_index')}")
                logger.info(f"失败原因 (reason): {result.get('error', {}).get('reason')}")
                logger.info(f"失败类型 (type): {result.get('error', {}).get('type')}")
                # Sometimes the deeper cause is here
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
            size=top_k,  # Fetch enough results for subsequent reranking
        )
        return response["hits"]["hits"]

    def perform_search_detailed(self, query, top_k=None):
        """
        Execute a query and return results with details such as similarity score and total hits.
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
            # _score represents similarity in vector-based queries
            source["_score"] = hit["_score"]
            results.append(source)

        return results, total_hits

    def get_index_mapping(self):
        """
        Get mapping information for the specified index.
        """
        # Use the indices.get_mapping method
        mapping = self.es_client.indices.get_mapping(index=self.index_name)
        mapping = mapping.get(self.index_name)
        return mapping["mappings"]

    def index_exists(self, index_name: Optional[str] = None) -> bool:
        """
        Check whether the specified index exists.

        :param index_name: Index name to check; if None, use the instance `self.index_name`.
        :return: Return True if it exists, otherwise False, including exceptions which are logged.
        """
        idx = index_name or self.index_name
        try:
            return self.es_client.indices.exists(index=idx)
        except Exception as e:
            logger.exception(f"检查索引存在性时出错: {idx} - {e}")
            return False

    def delete_index(self):
        """
        Delete the specified index.
        """
        # Use the indices.delete method
        # ignore_unavailable=True means no error is raised if the index does not exist
        response = self.es_client.indices.delete(index=self.index_name, ignore_unavailable=True)
        if response.get("acknowledged"):
            return True
        else:
            # This usually does not happen when ignore_unavailable=True, except for permission issues and similar cases
            return False

    def create_index(self, settings: dict = None):
        """
        Create a new index and optionally specify mappings and settings.
        """
        # First check whether the index already exists
        if self.es_client.indices.exists(index=self.index_name):
            logger.info(f"索引 '{self.index_name}' 已经存在，无需创建。")
            return False

        # Use the indices.create method to create the index
        # Mappings and settings are passed as parameters
        response = self.es_client.indices.create(index=self.index_name, mappings=self.mappings, settings=settings)

        if response.get("acknowledged"):
            logger.info(f"索引 '{self.index_name}' 创建成功。")
            return True
        else:
            logger.info(f"索引 '{self.index_name}' 创建失败。")
            return False

    def recreate_index(self, settings: dict = None):
        """
        Recreate the index: delete it if it exists, then create a new one.
        """
        # Delete the existing index
        self.delete_index()
        # Create a new index
        return self.create_index(settings)

    def count_documents(self) -> int:
        """
        Count documents in the index.
        """
        try:
            response = self.es_client.count(index=self.index_name)
            return response["count"]
        except Exception as e:
            logger.error(f"统计索引文档数量时出错: {self.index_name} - {e}")
            return 0
