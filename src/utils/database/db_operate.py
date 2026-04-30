from peewee_async import AioModel
from peewee import fn

async def get_all(model: AioModel):
    """Get all records"""
    return await model.select().aio_execute()

async def get_recors_group(model: AioModel, group_by_field: str):
    """Get records grouped by the specified field"""
    query = model.select(getattr(model, group_by_field)).group_by(getattr(model, group_by_field))
    return await query.aio_execute()

async def get_records_group_with_count(model: AioModel, group_by_field: str):
    """Group by the specified field and count records"""
    query = model.select(getattr(model, group_by_field), fn.COUNT(model.id).alias('count')).group_by(getattr(model, group_by_field))
    return await query.aio_execute()