import asyncio
import datetime
import time

from CeleryManage.scheduler import celery_app
from models.database.TaskModel import TaskModel
from models.database.TestModel import TestModel


async def _insert_test_data(record_id: str):
    async def insert_in_db(id: int):
        await TestModel.aio_create(id=id, create_time=datetime.datetime.now())

    _task, _ = await TaskModel.aio_get_or_create(id=record_id)
    _task.status = 1
    _task.update_time = datetime.datetime.now()
    await _task.aio_save()
    num = 1000000
    start = time.time()
    for i in range(0, num):
        await insert_in_db(i)
    end = time.time()

    return {"num": num, "time": end - start}


@celery_app.task(name="task.db.insert_test_data", ignore_result=True)
def insert_test_data(record_id: str):
    # 获取列表
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    task = loop.create_task(_insert_test_data(record_id))
    loop.run_until_complete(task)
    return task.result()
