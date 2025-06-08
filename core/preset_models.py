from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ParameterMapping:
    name: str
    path: str
    rangeMin: Optional[float] = None
    rangeMax: Optional[float] = None


@dataclass
class Macro:
    index: int
    name: str
    parameters: List[ParameterMapping] = field(default_factory=list)
    value: Any = None
