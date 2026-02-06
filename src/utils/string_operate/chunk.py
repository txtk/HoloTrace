import re
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from typing import List, Dict
import unicodedata

def clean_cti_text(text: str) -> str:
    """
    专门针对威胁情报文本的清洗函数。
    1. 标准化 Unicode 字符。
    2. 移除表格行、分割线、以及无用的元数据行。
    3. 清洗不可见字符和多余的装饰性符号。
    4. 保留 IOC (IP, URL, Hash, Snort Rules) 所需的关键符号。
    """
    if not text:
        return ""

    # --- 步骤 1: Unicode 标准化 (NFKC) ---
    # 这会将全角字符转为半角 (e.g., １２３ -> 123)，并处理特殊空格 (\xa0 -> space)
    text = unicodedata.normalize('NFKC', text)

    # --- 步骤 2: 定义正则模式 ---
    
    # 模式A: 匹配表格行 (包含多个管道符，或者以管道符开头结尾)
    # 逻辑：如果一行包含超过2个管道符，且看起来像表格结构，则视为噪音
    # 注意：需小心 Snort 规则 (e.g. content:"|3a 20|")，所以不能简单统计管道符
    # 这里使用严格的表格行特征：以 | 开头 或 结尾，且中间还有 |
    table_line_pattern = re.compile(r'^\s*\|.*\|.*\|\s*$|^\s*\|[-: ]+\|\s*$')

    # 模式B: 匹配分割线 (连续的 - = _ *)
    separator_pattern = re.compile(r'^\s*[-=_*]{3,}\s*$')

    # 模式C: 匹配常见的噪音废话 (不区分大小写)
    noise_keywords = [
        r"click here", 
        r"all rights reserved", 
        r"copyright", 
        r"revisions?", 
        r"contact information",
        r"pdf version",
        r"this product is provided subject to"
    ]
    # 组合成一个正则
    boilerplate_pattern = re.compile(r'|'.join(noise_keywords), re.IGNORECASE)

    # --- 步骤 3: 按行处理 (结构清洗) ---
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped_line = line.strip()
        
        # 跳过空行（稍后统一处理换行）
        if not stripped_line:
            # 可以在这里保留一个空行占位符，如果需要保留段落结构
            cleaned_lines.append("") 
            continue

        # 1. 过滤表格
        if table_line_pattern.match(stripped_line):
            continue
            
        # 2. 过滤分割线
        if separator_pattern.match(stripped_line):
            continue

        # 3. 过滤废话行 (仅当该行很短且包含关键词时，防止误删正文)
        if len(stripped_line) < 100 and boilerplate_pattern.search(stripped_line):
            continue

        # 4. 修复断行 (针对 PDF 复制粘贴常见的单词断行，如 "attac-\nker")
        # 这一步比较激进，如果您的文本主要是网页抓取，可以注释掉
        if stripped_line.endswith('-') and len(cleaned_lines) > 0 and cleaned_lines[-1] != "":
             # 将上一行末尾的连字符去掉，并与当前行合并
             # 注意：这是一个简化的处理，实际工程中可能需要字典校验
             pass # 暂不开启，防止误删正常的连字符，视具体情况而定

        cleaned_lines.append(stripped_line)

    # 重组文本
    text = '\n'.join(cleaned_lines)

    # --- 步骤 4: 字符级清洗 (符号清洗) ---

    # 1. 清除控制字符 (Control Characters)，保留 \n, \t, \r
    # range \x00-\x08, \x0b-\x0c, \x0e-\x1f
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 2. 清除装饰性列表符号 (Bullet points)，统一为标准的 Markdown 符号或去除
    # 例如：●, ■, ◆, ➤, ➢, ->, etc. 替换为简单的 "-"
    # 注意：不要替换 [], {}, (), |, ., : 等技术符号
    text = re.sub(r'^\s*[●■◆➤➢▶]\s*', '- ', text, flags=re.MULTILINE)

    # 3. 压缩多余空白 (将连续的2个以上空格变为1个，但保留换行)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 4. 压缩连续换行 (将3个以上换行变为2个，保留段落感)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

class CTIProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 定义需要提升为标题的关键词映射
        # 作用：将非结构化文本转化为 Markdown 结构，便于分片
        self.header_mappings = [
            # 报告类结构
            (r"(?i)^(summary|executive summary)", "## Summary"),
            (r"(?i)^(technical details|analysis)", "## Technical Analysis"),
            (r"(?i)^(mitigations?|recommendations?)", "## Mitigations"),
            (r"(?i)^(indicators?|iocs?|signatures?)", "## IOCs"),
            # 时间线类结构 (针对文章一)
            (r"(?i)^(january|february|march|april|may|june|july|august|september|october|november|december)(.*)", r"## Timeline: \1\2"),
        ]

    def _inject_structure(self, text: str) -> str:
        """
        预处理：扫描文本，将特定的关键词行转换为 Markdown 二级标题 (##)。
        """
        for pattern, replacement in self.header_mappings:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text

    def process(self, text: str, source_name: str = "Unknown") -> List[Dict]:
        """
        主流程：清洗 -> 结构化 -> 分片 -> 封装
        """
        # 1. 清洗
        cleaned_text = clean_cti_text(text)
        
        # 2. 注入结构 (伪 Markdown 化)
        structured_text = self._inject_structure(cleaned_text)

        # 3. 第一阶段分片：基于 Header (逻辑分片)
        headers_to_split_on = [("##", "Section")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_docs = markdown_splitter.split_text(structured_text)

        # 4. 第二阶段分片：基于字符数 (物理分片)
        # 使用递归分片器处理过长的 Section
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            # 分隔符优先级：双换行 > 单换行 > 句号后 > 空格
            # 这里的 (?<=\. ) 保证句子完整性
            separators=["\n\n", "\n", "(?<=\. )", " ", ""],
            is_separator_regex=True
        )
        
        final_docs = recursive_splitter.split_documents(md_docs)

        # 5. 结果封装与元数据增强
        results = []
        for doc in final_docs:
            content = doc.page_content.strip()
            # 忽略过短的碎片
            if len(content) < 10: 
                continue

            section = doc.metadata.get("Section", "General")
            
            # 构造结构化数据
            chunk_data = {
                "source": source_name,
                "section": section,
                "content": content,
                # 组合一个用于向量化的完整文本 (Text Representation)
                "embedding_text": f"Source: {source_name} | Section: {section} | Content: {content}"
            }
            results.append(chunk_data)

        return results