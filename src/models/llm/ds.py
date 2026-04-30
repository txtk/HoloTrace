from openai import OpenAI

from config import settings


class DS:
    def __init__(self):
        self.client = OpenAI(base_url=settings.ds_url, api_key=settings.ds_api_key)

    def send_request_poml(self, poml_content):
        response = self.client.chat.completions.create(
            **poml_content,
            model=settings.ds_model_name,
            temperature=settings.temperature,
            stream=False,
            # extra_body={"thinking": {
            #     "type": "enabled",
            # }},
        )
        import utils.llm_use
        if hasattr(response, 'usage') and response.usage:
            utils.llm_use.total_tokens_used += response.usage.total_tokens
        return self.result_handler(response)

    def result_handler(self, response):
        result = response.choices[0].message.content
        return result

ds = DS()

