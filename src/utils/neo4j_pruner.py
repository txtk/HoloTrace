from loguru import logger
from config import neo4j_driver, neo4j_driver_sub
from neo4j import AsyncTransaction

class Neo4jPruner:
    """
    一个用于连接Neo4j并执行图剪枝操作的类。
    """
    def __init__(self, neo4j_type):

        if neo4j_type == "source":
            driver = neo4j_driver
        else:
            driver = neo4j_driver_sub
        self._driver = driver

    def close(self):
        """关闭数据库连接"""
        if self._driver is not None:
            self._driver.close()
            logger.info("数据库连接已关闭。")


    async def execute_pruning(self, high_level_label, low_level_label, intermediate_label):
        """
        第二步：执行剪枝操作，删除已识别的“捷径”关系。
        """
        if not self._driver:
            return 0
            
        # 这是核心的Cypher删除查询
        query = f"""
        // 匹配与查找步骤中完全相同的模式
        MATCH (c:`{low_level_label}`)-[r]-(a:`{high_level_label}`)
        WHERE EXISTS {{
          MATCH (a)-[]-(b:`{intermediate_label}`)-[]-(c)
        }}
        
        
        // 返回被删除的关系数量
        RETURN count(r) AS deleted_count
        """
        
        logger.warning("即将执行删除操作！请确保已备份数据。")
        
        async with self._driver.session() as session:
            # 使用事务来执行写操作
            result = await session.execute_write(self._run_delete_query, query)
            deleted_count = result if result is not None else 0
            logger.info(f"操作完成，成功删除了 {deleted_count} 个冗余关系。")
            return deleted_count

    @staticmethod
    async def _run_delete_query(tx: AsyncTransaction, query):
        result = await tx.run(query)
        record = await result.single()
        return record["deleted_count"] if record else 0

