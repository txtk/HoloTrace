from typing import List

from openai import APIError, OpenAI

from config import settings


class Embedding:
    def __init__(self):
        self.client = OpenAI(base_url=settings.base_url_em, api_key=settings.sc_api_key[0])

    def embed_query(self, text: str, dimensions) -> List[float]:
        """
        为单个查询文本生成向量。

        参数:
            text (str): 需要向量化的单个查询文本。

        返回:
            List[float]: 代表该查询文本的向量。
        """
        if not isinstance(text, str):
            print("输入内容不对: ", text)
            raise TypeError("输入必须是一个字符串。")

        try:
            response = self.client.embeddings.create(
                model=settings.embedding,
                input=[text],  # API需要一个列表作为输入
                dimensions=dimensions,
            )
            return response.data[0].embedding
        except APIError as e:
            print(f"调用API时发生错误: {e}")
            raise

    def embed_documents(self, texts: List[str], dimensions) -> List[List[float]]:
        """
        为多个文本生成向量，支持批次处理（每批最多100个）。

        参数:
            texts (List[str]): 需要向量化的文本列表。

        返回:
            List[List[float]]: 代表这些文本的向量列表。
        """
        if not isinstance(texts, list):
            raise TypeError("输入必须是一个列表。")

        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=settings.embedding,
                    input=batch,
                    dimensions=dimensions,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except APIError as e:
                print(f"调用API时发生错误: {e}")
                raise

        return all_embeddings


embedding = Embedding()
