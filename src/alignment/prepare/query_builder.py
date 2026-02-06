from typing import Any, List

from utils.vector.query_builders import (
    BoolQueryBuilder,
    ExistsQueryBuilder,
    KNNQueryBuilder,
    MatchQueryBuilder,
    TermQueryBuilder,
    TermsQueryBuilder,
)


class QueryBuilder:
    # 优先级配置：字段名 -> 权重
    PRIORITY_BOOSTS = {"related_groups": 0.1, "related_malwares": 0.1, "related_attcks": 0.1}

    def _apply_priority_boosts(self, bool_builder: BoolQueryBuilder):
        """为查询应用预设的优先级权重"""
        for field, boost in self.PRIORITY_BOOSTS.items():
            bool_builder.add_should(ExistsQueryBuilder(field, boost=boost))
        return bool_builder

    def build_match_query(self, field_name: str, content: str, priority: bool = True):
        """构建全文匹配查询"""
        bool_builder = BoolQueryBuilder()
        bool_builder.add_must(MatchQueryBuilder(field=field_name, query=content))

        if priority:
            self._apply_priority_boosts(bool_builder)

        return bool_builder.get_query()

    def build_term_query(self, field_name: str, value: Any, priority: bool = True):
        """构建精确匹配查询 (单个值)"""
        bool_builder = BoolQueryBuilder()
        bool_builder.add_must(TermQueryBuilder(field=field_name, value=value))

        if priority:
            self._apply_priority_boosts(bool_builder)

        return bool_builder.get_query()

    def build_terms_query(self, field_name: str, values: List[Any], priority: bool = True):
        """构建精确匹配查询 (多个值)"""
        bool_builder = BoolQueryBuilder()
        bool_builder.add_must(TermsQueryBuilder(field=field_name, values=values))

        if priority:
            self._apply_priority_boosts(bool_builder)

        return bool_builder.get_query()

    def build_knn_query(self, vector_field: str, query_vector: List[float], k: int = 10, num_candidates: int = 100, priority: bool = True):
        """构建向量查询"""
        bool_builder = BoolQueryBuilder()
        bool_builder.add_must(KNNQueryBuilder(vector_field, query_vector, k, num_candidates))
        if priority:
            self._apply_priority_boosts(bool_builder)
        return bool_builder.get_query()