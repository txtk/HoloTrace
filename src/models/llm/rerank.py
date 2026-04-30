from typing import List

from openai import APIError, OpenAI

from config import settings


class Ranker:
    def __init__(self):
        self.client = OpenAI(base_url=settings.base_url, api_key=settings.api_key)

    def rank_query(self, embedding: dict) -> List[float]:
        try:
            response = self.client.chat.completions.create(
                model=settings.rerank,
                messages=[{"role": "user", "content": embedding}],  # The API expects a list as input
            )
            return response.data[0].embedding
        except APIError as e:
            print(f"调用API时发生错误: {e}")
            raise


rank = Ranker()

rank.rank_query(
    {
        "query": "What is the capital of France?",
        "documents": ["Paris is the capital of France.", "London is a large city in the UK."],
        "top_n": 1,
    }
)
