"""Domain model for a long-term memory."""
from dataclasses import dataclass


@dataclass
class Memory:
    key: str                 # stable identifier, e.g. 'career_goal'
    category: str            # topic bucket used by retrieval, e.g. 'career'
    value: str               # the remembered text
    confidence: float = 0.8  # 0..1, how sure the rule is; used for ranking
