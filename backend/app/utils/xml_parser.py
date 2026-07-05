from lxml import etree
from typing import Dict, List, Optional
import re

def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_pmc_xml(xml_content: str) -> Dict[str, List[str]]:
    """
    Parses PMC XML and extracts specific sections.
    Returns a dictionary: {"discussion": [], "limitations": [], "conclusion": [], "future_directions": []}
    """
    sections = {
        "discussion": [],
        "limitations": [],
        "conclusion": [],
        "future_directions": []
    }

    try:
        # Recover=True allows parsing slightly malformed XML
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(xml_content.encode('utf-8'), parser=parser)

        # PMC XML typically has <body> <sec> tags.
        # We look for <sec> tags and check their <title>
        for sec in root.findall(".//sec"):
            title_elem = sec.find("title")
            if title_elem is not None and title_elem.text:
                title_text = title_elem.text.lower()

                category = None
                if "discussion" in title_text:
                    category = "discussion"
                elif "limit" in title_text:
                    category = "limitations"
                elif "conclu" in title_text:
                    category = "conclusion"
                elif "future" in title_text or "direction" in title_text:
                    category = "future_directions"

                if category:
                    # Extract paragraphs <p>
                    for p in sec.findall(".//p"):
                        # Extract text, stripping inner tags (like <xref> for citations)
                        text = "".join(p.itertext())
                        cleaned = clean_text(text)
                        if cleaned:
                            sections[category].append(cleaned)

        return sections
    except Exception as e:
        # Log error in production
        return sections
