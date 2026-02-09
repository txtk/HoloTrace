import sys
from collections import defaultdict
from loguru import logger

def find_directed_links(file_path):
    # 使用 defaultdict(list)，因为一个实体可以有多个（重复的）出向/入向链接
    # 例如 (e1, r1, e2) 和 (e1, r2, e2) 是两条不同的出向链接
    outgoing_links = defaultdict(list)
    incoming_links = defaultdict(list)
    
    # 我们需要一个集合来跟踪所有见过的实体
    all_entities = set()
    
    logger.info(f"--- 正在处理文件 (有向图模式): {file_path} ---")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                
                if len(parts) == 3:
                    try:
                        e1 = int(parts[0])
                        r = int(parts[1])  # 现在我们保留关系
                        e2 = int(parts[2])
                        
                        # 将实体ID添加到总集合中
                        all_entities.add(e1)
                        all_entities.add(e2)
                        
                        # --- 核心逻辑 (有向图) ---
                        # 1. 存储出向链接：e1 -> e2 (通过 r)
                        outgoing_links[e1].append((r, e2))
                        
                        # 2. 存储入向链接：e1 -> e2 (等同于 e2 <- e1)
                        incoming_links[e2].append((r, e1))
                        
                    except ValueError:
                        logger.info(f"警告: 第 {i+1} 行格式错误 (非数字)，已跳过: '{line}'", file=sys.stderr)
                else:
                    logger.info(f"警告: 第 {i+1} 行格式错误 (非3列)，已跳过: '{line}'", file=sys.stderr)

    except FileNotFoundError:
        logger.info(f"错误: 文件未找到 '{file_path}'", file=sys.stderr)
        return None, None, None
    except Exception as e:
        logger.info(f"读取文件时发生未知错误: {e}", file=sys.stderr)
        return None, None, None

    logger.info(f"--- 处理完成 ---")
    return outgoing_links, incoming_links, all_entities