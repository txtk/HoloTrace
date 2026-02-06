from peewee_async import AioModel
from peewee import fn

async def get_all(model: AioModel):
    """获取所有记录"""
    return await model.select().aio_execute()

async def get_recors_group(model: AioModel, group_by_field: str):
    """按指定字段分组获取记录"""
    query = model.select(getattr(model, group_by_field)).group_by(getattr(model, group_by_field))
    return await query.aio_execute()

async def get_records_group_with_count(model: AioModel, group_by_field: str):
    """按指定字段分组并统计数量"""
    query = model.select(getattr(model, group_by_field), fn.COUNT(model.id).alias('count')).group_by(getattr(model, group_by_field))
    return await query.aio_execute()