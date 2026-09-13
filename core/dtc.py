from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DTC:
    """Representa um código de falha já descodificado e catalogado."""

    code: str
    description: str
    category: str            # nome legível ("Travagem / Chassis (inclui ABS)")
    category_letter: str      # "P" / "C" / "B" / "U"
    generic: bool = True
    status: str = "Confirmado"          # Confirmado / Pendente
    freeze_frame: Optional[Dict] = field(default=None)

    @property
    def origin_label(self):
        return "SAE genérico" if self.generic else "Específico do fabricante"
