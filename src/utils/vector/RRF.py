class RRF:
    def __init__(self):
        self.query = {
            "retriever": {
                "rrf": {
                    "retrievers": [],
                }
            }
        }

    def add_retrievers(self, retrievers):
        for retriver in retrievers:
            self.query["retriever"]["rrf"]["retrievers"].append(retriver.get_query())
        return self

    def get_query(self):
        return self.query


class RRF_Retriever:
    def __init__(self):
        self.query = {"standard": {"query": {}}}

    def get_query(self):
        return self.query


class RRF_Keyword_Retriever(RRF_Retriever):
    def __init__(self, item_name="keyword", keywords=""):
        super().__init__()
        query = {"terms": {item_name: keywords}}
        self.query["standard"]["query"] = query


class RRF_Match_Retriever(RRF_Retriever):
    def __init__(self, item_name="content", content=""):
        super().__init__()
        query = {"match": {item_name: {"query": content}}}
        self.query["standard"]["query"] = query


class RRF_Exists_Retriever(RRF_Retriever):
    """
    是否存在某字段的检索器，用于提升拥有特定属性的文档排名
    """

    def __init__(self, field: str, boost: float = 1.0):
        super().__init__()
        self.query["standard"]["query"] = {"exists": {"field": field, "boost": boost}}


class RRF_Semantic_Retriever(RRF_Retriever):
    def __init__(self, item_name="semantic", content=""):
        super().__init__()
        query = {
            item_name: {
                "field": "semantic",
                "query": content,
            }
        }
        self.query["standard"]["query"] = query


class RRF_Vector_Retriever(RRF_Retriever):
    """
    针对 dense_vector 字段封装的向量检索器
    """

    def __init__(self, vector_field="semantic", query_vector=None):
        super().__init__()
        # 移除父类默认生成的空 standard 查询，避免 ES 解析错误
        if "standard" in self.query:
            del self.query["standard"]

        # 对于 dense_vector 字段，不能再使用普通的 'match' 或 'semantic' 查询语句
        # 必须使用 'knn' 语法来查询 [2]
        knn_query = {
            "field": vector_field,
            "query_vector": query_vector,  # 这里必须是你的模型生成的 4096 维浮点数组
            "k": 10,  # 最终返回的最近邻文档数
            "num_candidates": 100,  # 每个分片检索的候选文档数，建议为 k 的 10 倍左右
        }

        # 在 RRF (Reciprocal Rank Fusion) 架构中，
        # 通常会将向量查询作为一个独立的分支与标准查询结合 [1]
        # 注意：这里假设你的父类结构支持直接赋值 knn
        self.query["knn"] = knn_query
