from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

class InvoiceLabel(BaseModel):
    doc_type: Literal["invoice", "receipt", "other"]
    language: Literal["en", "sv", "fi"]
    supplier: str = Field(min_length=1)
    invoice_number: Optional[str] = None
    invoice_date: date
    currency: Literal["EUR", "SEK", "GBP"]
    total: Decimal = Field(ge=0, decimal_places=2)
    vat_amount: Decimal = Field(ge=0, decimal_places=2)

    @model_validator(mode="after")
    def vat_not_above_total(self):
        if self.vat_amount > self.total:
            raise ValueError("vat_amount cannot exceed total")
        return self