"""Pure scoring functions — one file per instrument.

Each function:
- Accepts raw items (list of ints), NOT a pydantic model.
- Raises ``InvalidResponseError`` on the first validation failure — no partial scoring.
- Returns a typed result dataclass with ``total``, ``severity``, and per-item echo.
- Is a ``@dataclass(frozen=True)`` output, never a mutable dict.

Reference values for severity thresholds come from the published validation papers.
See ``scoring_tests/`` for the machine-checked fidelity suite.
"""

from .audit_c import AuditCResult, score_audit_c
from .cssrs import CssrsResult, score_cssrs_screen
from .dast10 import Dast10Result, score_dast10
from .phq9 import Phq9Result, score_phq9
from .gad7 import Gad7Result, score_gad7
from .pss10 import Pss10Result, score_pss10
from .who5 import Who5Result, score_who5

__all__ = [
    "AuditCResult",
    "CssrsResult",
    "Dast10Result",
    "Gad7Result",
    "Phq9Result",
    "Pss10Result",
    "Who5Result",
    "score_audit_c",
    "score_cssrs_screen",
    "score_dast10",
    "score_gad7",
    "score_phq9",
    "score_pss10",
    "score_who5",
]
