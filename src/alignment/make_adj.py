import sys
from collections import defaultdict
from loguru import logger

def find_directed_links(file_path):
    """
        Read data from a directed triples file and build two adjacency lists:
        1. Store outgoing links for each entity (outgoing).
        2. Store incoming links for each entity (incoming).
        
        Data structure:
        - Key: entity ID (int)
        - Value: a list containing multiple tuples
        - Tuple format: (relationship_id, neighbor_id)
        
        Args:
            file_path (str): Path to the .txt file containing triples.
        
        Returns:
            tuple: (outgoing_links, incoming_links, all_entities)
            - outgoing_links (dict): dictionary that stores outgoing links
            - incoming_links (dict): dictionary that stores incoming links
            - all_entities (set): set containing all entity IDs
    """
    # Use defaultdict(list) because one entity can have multiple, possibly duplicate, outgoing/incoming links
    # For example, (e1, r1, e2) and (e1, r2, e2) are two different outgoing links
    outgoing_links = defaultdict(list)
    incoming_links = defaultdict(list)
    
    # Use a set to track all seen entities
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
                        r = int(parts[1])  # Keep the relationship now
                        e2 = int(parts[2])
                        
                        # Add entity IDs to the global set
                        all_entities.add(e1)
                        all_entities.add(e2)
                        
                        # --- Core logic (directed graph) ---
                        # 1. Store outgoing links: e1 -> e2 (through r)
                        outgoing_links[e1].append((r, e2))
                        
                        # 2. Store incoming links：e1 -> e2 (equivalent to e2 <- e1)
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