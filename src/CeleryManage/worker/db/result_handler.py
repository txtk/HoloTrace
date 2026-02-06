from loguru import logger


async def result_handler(result_data: dict):
    # 模拟结果处理逻辑
    logger.info(f"处理数据条数：{result_data.get('num', 0)}, 耗时：{result_data.get('time', 0)}秒")
    return result_data
