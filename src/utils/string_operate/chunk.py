import re
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from typing import List, Dict
import unicodedata

def clean_cti_text(text: str) -> str:
    """
    Cleaning function tailored for threat intelligence text.
    1. Normalize Unicode characters.
    2. Remove table rows, separators, and useless metadata lines.
    3. Clean invisible characters and extra decorative symbols.
    4. Preserve key symbols needed for IOCs (IP, URL, Hash, Snort Rules).
    """
    if not text:
        return ""

    # --- Step 1: Unicode normalization (NFKC) ---
    # This converts full-width characters to half-width characters (e.g., 123 -> 123) and handles special spaces (\xa0 -> space)
    text = unicodedata.normalize('NFKC', text)

    # --- Step 2: Define regex patterns ---
    
    # Pattern A: match table rows that contain multiple pipes or start/end with a pipe
    # Logic: if a line contains more than two pipes and looks like a table, treat it as noise
    # Note: be careful with Snort rules (e.g. content:"|3a 20|"); do not simply count pipe characters
    # Use strict table-row features here: starts or ends with | and has another | in the middle
    table_line_pattern = re.compile(r'^\s*\|.*\|.*\|\s*$|^\s*\|[-: ]+\|\s*$')

    # Pattern B: match separators (consecutive - = _ *)
    separator_pattern = re.compile(r'^\s*[-=_*]{3,}\s*$')

    # Pattern C: match common noisy filler text (case-insensitive)
    noise_keywords = [
        r"click here", 
        r"all rights reserved", 
        r"copyright", 
        r"revisions?", 
        r"contact information",
        r"pdf version",
        r"this product is provided subject to"
    ]
    # Combine into one regex
    boilerplate_pattern = re.compile(r'|'.join(noise_keywords), re.IGNORECASE)

    # --- Step 3: process by line (structural cleaning) ---
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped_line = line.strip()
        
        # Skip empty lines; newlines are normalized later
        if not stripped_line:
            # A blank-line placeholder can be kept here if paragraph structure should be preserved
            cleaned_lines.append("") 
            continue

        # 1. Filter tables
        if table_line_pattern.match(stripped_line):
            continue
            
        # 2. Filter separators
        if separator_pattern.match(stripped_line):
            continue

        # 3. Filter filler lines only when the line is short and contains keywords, to avoid deleting body text by mistake
        if len(stripped_line) < 100 and boilerplate_pattern.search(stripped_line):
            continue

        # 4. Fix broken lines, such as word breaks common in PDF copy-paste like "attac-\nker"
        # This step is aggressive; comment it out if your text mostly comes from web scraping
        if stripped_line.endswith('-') and len(cleaned_lines) > 0 and cleaned_lines[-1] != "":
             # Remove the trailing hyphen from the previous line and merge with the current line
             # Note: this is a simplified treatment; real projects may need dictionary validation
             pass # Disabled for now to avoid removing normal hyphens; adjust as needed

        cleaned_lines.append(stripped_line)

    # Reassemble text
    text = '\n'.join(cleaned_lines)

    # --- Step 4: character-level cleaning (symbol cleaning) ---

    # 1. Remove control characters while keeping \n, \t, and \r
    # range \x00-\x08, \x0b-\x0c, \x0e-\x1f
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 2. Remove decorative bullet symbols and normalize them to standard Markdown symbols or remove them
    # For example: replace bullets such as dot, square, diamond, arrow, or -> with a simple "-"
    # Note: do not replace technical symbols such as [], {}, (), |, ., or :
    text = re.sub(r'^\s*[●■◆➤➢▶]\s*', '- ', text, flags=re.MULTILINE)

    # 3. Collapse extra whitespace by replacing runs of more than two spaces with one space while preserving newlines
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 4. Collapse consecutive newlines by replacing three or more newlines with two to preserve paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

class CTIProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Define keyword mappings to promote to headings
        # Purpose: convert unstructured text into Markdown structure for easier chunking
        self.header_mappings = [
            # Report-style structure
            (r"(?i)^(summary|executive summary)", "## Summary"),
            (r"(?i)^(technical details|analysis)", "## Technical Analysis"),
            (r"(?i)^(mitigations?|recommendations?)", "## Mitigations"),
            (r"(?i)^(indicators?|iocs?|signatures?)", "## IOCs"),
            # Timeline-style structure for article one
            (r"(?i)^(january|february|march|april|may|june|july|august|september|october|november|december)(.*)", r"## Timeline: \1\2"),
        ]

    def _inject_structure(self, text: str) -> str:
        """
        Preprocess: scan text and convert specific keyword lines into Markdown level-2 headings (##).
        """
        for pattern, replacement in self.header_mappings:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text

    def process(self, text: str, source_name: str = "Unknown") -> List[Dict]:
        """
        Main flow: clean -> structure -> chunk -> wrap
        """
        # 1. Clean
        cleaned_text = clean_cti_text(text)
        
        # 2. Inject structure (pseudo-Markdown conversion)
        structured_text = self._inject_structure(cleaned_text)

        # 3. Stage 1 chunking: based on headers (logical chunking)
        headers_to_split_on = [("##", "Section")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_docs = markdown_splitter.split_text(structured_text)

        # 4. Stage 2 chunking: based on character count (physical chunking)
        # Use a recursive splitter for oversized sections
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            # Separator priority: double newline > single newline > after period > space
            # The (?<=\. ) here preserves sentence integrity
            separators=["\n\n", "\n", "(?<=\. )", " ", ""],
            is_separator_regex=True
        )
        
        final_docs = recursive_splitter.split_documents(md_docs)

        # 5. Result wrapping and metadata enrichment
        results = []
        for doc in final_docs:
            content = doc.page_content.strip()
            # Ignore chunks that are too short
            if len(content) < 10: 
                continue

            section = doc.metadata.get("Section", "General")
            
            # Build structured data
            chunk_data = {
                "source": source_name,
                "section": section,
                "content": content,
                # Combine a complete text representation for vectorization
                "embedding_text": f"Source: {source_name} | Section: {section} | Content: {content}"
            }
            results.append(chunk_data)

        return results