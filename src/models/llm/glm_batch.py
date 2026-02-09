# from zai import ZhipuAiClient
# from utils.file.path_utils import PathUtils
# from config import settings
# import copy
# import poml
# import pandas as pd
# from loguru import logger
# import time

# class ZhipuBatch:
#     client = ZhipuAiClient(api_key=settings.zhipu_api_key)
#     batch_file_path = PathUtils.path_concat(settings.json_dir, "zhipu_batch.jsonl")
#     result_file_path = PathUtils.path_concat(settings.json_dir, "zhipu_batch_result.jsonl")

#     base_format = {
#         "custom_id": "",
#         "method": "POST",
#         "url": f"{settings.zhipu_batch_url}",
#         "body": {
#             "model": f"{settings.zhipu_model_name}",
#             "messages": [],
            
#         },
#         "stream": False,
#         "thinking": {
#             "type": "enabled"
#         },
#         "temperature": settings.temperature
#     }

#     def make_batch_file(self, prompt_path, contexts):
#         contents = []
#         prompts = [poml.poml(prompt_path, context=context, format="openai_chat") for context in contexts]
#         for i, prompt in enumerate(prompts):
#             base_format = copy.deepcopy(self.base_format)
#             base_format["body"]["messages"] = prompt["messages"]
#             base_format["custom_id"] = f"request-{i+1}"
#             contents.append(base_format)
#         df = pd.DataFrame(contents)
#         df.to_json(self.batch_file_path, orient="records", lines=True, force_ascii=False)
        

#     def handle_batch(self):
#         file_object = self.client.files.create(
#             file=open(self.batch_file_path, "rb"),
#             purpose="batch"
#         )
#         logger.info(file_object)

#         batch = self.client.batches.create(
#             input_file_id=file_object.id,
#             endpoint="/v4/chat/completions",
#             auto_delete_input_file=True,
#             metadata={
#                 "description": "商品评价情感分析",
#                 "project": "sentiment_analysis"
#             }
#         )
#         logger.info(batch)
#         self.batch = batch

#     def check_batch_status(self):
#         while True:
#             batch_status = self.client.batches.retrieve(self.batch.id)
#             print(f"任务状态: {batch_status.status}")
            
#             if batch_status.status == "completed":
#                 result_content = self.client.files.content(batch_status.output_file_id)
#                 result_content.write_to_file(self.result_file_path)
#                 return True
            
#             elif batch_status.status in ["failed", "expired", "cancelled"]:
#                 print(f"任务失败，状态: {batch_status.status}")
#                 return False
#             time.sleep(30)  # 等待30秒后再次检查


#     def parse_results(self):
#         results = []
#         df = pd.read_json(self.result_file_path, lines=True)
#         for index, row in df.iterrows():
#             result = row["response"]
#             if row["status_code"] == 200:
#                 result_content = result["body"]['choices'][0]['message']['content']
#                 result_content = result_content.split("</think>")[1].strip()
#                 results.append(result_content)
#             else:
#                 raise("请求失败")
#         return results
    