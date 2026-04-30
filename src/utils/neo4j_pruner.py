from loguru import logger
from config import neo4j_driver, neo4j_driver_sub
from neo4j import AsyncTransaction

class Neo4jPruner:
    """
    A class for connecting to Neo4j and performing graph pruning.
    """
    def __init__(self, neo4j_type):

        if neo4j_type == "source":
            driver = neo4j_driver
        else:
            driver = neo4j_driver_sub
        self._driver = driver

    def close(self):
        """Close the database connection"""
        if self._driver is not None:
            self._driver.close()
            logger.info("数据库连接已关闭。")


    async def execute_pruning(self, high_level_label, low_level_label, intermediate_label):
        """
        Step 2: perform pruning and delete identified shortcut relationships.
        """
        if not self._driver:
            return 0
            
        # This is the core Cypher delete query
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
            # Use a transaction to execute the write operation
            result = await session.execute_write(self._run_delete_query, query)
            deleted_count = result if result is not None else 0
            logger.info(f"操作完成，成功删除了 {deleted_count} 个冗余关系。")
            return deleted_count

    @staticmethod
    async def _run_delete_query(tx: AsyncTransaction, query):
        result = await tx.run(query)
        record = await result.single()
        return record["deleted_count"] if record else 0

