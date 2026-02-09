from openai import OpenAI

from config import settings


class SC:
    def __init__(self, api_key):
        self.client = OpenAI(base_url=settings.sc_url, api_key=api_key)

    def send_request_poml(self, poml_content):
        response = self.client.chat.completions.create(
            **poml_content,
            model=settings.sc_model_name,
            temperature=settings.temperature,
            stream=False,
            extra_body={"thinking": {
                "type": "enabled",
            }},
        )
        return self.result_handler(response)

    def result_handler(self, response):
        result = response.choices[0].message.content
        return result

scs = []
for i in settings.sc_api_key:
    sc = SC(api_key=i)
    scs.append(sc)
