# from CeleryManage.worker.db.result_handler import result_handler
# from data_analysis.get_opencti.worker import NAME_MAP as opencti_name_map
# from data_analysis.get_opencti.worker import WORKER_MAP as opencti_worker_map
# from data_analysis.opencti_statistic.worker import WORKER_MAP as opencti_neo4j_map
# from entity_alignment import WORKER_MAP as entity_alignment_map
# from data_process import WORKER_MAP as data_process_worker_map
from utils import WORKER_MAP as utils_worker_map
from data_process import WORKER_MAP as data_process_worker_map
from alignment import WORKER_MAP as alignment_worker_map

WORKER_MAP = dict()
WORKER_MAP.update(data_process_worker_map)
WORKER_MAP.update(utils_worker_map)
WORKER_MAP.update(alignment_worker_map)
# WORKER_MAP.update(opencti_neo4j_map)
# WORKER_MAP.update(entity_alignment_map)
# WORKER_MAP.update(
#     {
#         "task.db.insert_test_data": {
#             "task_path": "CeleryManage.worker.db.operate_db.insert_test_data",
#             "result_handler": result_handler,
#         }
#     }
# )
NAME_MAP = dict()
# NAME_MAP.update(opencti_name_map)
# NAME_MAP.update(
#     {
#         "insert_test_data": {
#             "name": "task.db.insert_test_data",
#             "end_status": 10,  # 任务链结束状态
#         },
#     }
# )
