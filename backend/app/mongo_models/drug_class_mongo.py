from beanie import Document
from typing import Optional


class DrugClassDocument(Document):
    bnf_id: str
    name: str
    level: str  # chapter / section
    parent_id: Optional[str] = None

    class Settings:
        name = "drug_classes"
        indexes = ["bnf_id", "level"]
