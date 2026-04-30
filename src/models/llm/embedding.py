from typing import List

from openai import APIError, OpenAI

from config import settings


class Embedding:
    def __init__(self):
        self.client = OpenAI(base_url=settings.base_url_em, api_key=settings.sc_api_key[0])

    def embed_query(self, text: str, dimensions) -> List[float]:
        """
            Generate an embedding vector for a single query text.
            
            Args:
                text (str): Single query text to vectorize.
            
            Returns:
                List[float]: Vector representation of the query text.
        """
        if not isinstance(text, str):
            print("输入内容不对: ", text)
            raise TypeError("输入必须是一个字符串。")

        try:
            response = self.client.embeddings.create(
                model=settings.embedding,
                input=[text],  # The API expects a list as input
                dimensions=dimensions,
            )
            return response.data[0].embedding
        except APIError as e:
            print(f"调用API时发生错误: {e}")
            raise

    def embed_documents(self, texts: List[str], dimensions) -> List[List[float]]:
        """
            Generate embedding vectors for multiple texts, with batch processing support.
            
            Args:
                texts (List[str]): Text list to vectorize.
            
            Returns:
                List[List[float]]: Vector representations of the input texts.
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
