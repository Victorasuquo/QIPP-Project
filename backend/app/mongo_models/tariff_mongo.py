from beanie import Document
from typing import Optional
from datetime import datetime


class TariffPriceDocument(Document):
    vmpp_id: str = ""
    vmpp: str = ""
    product: str = ""
    tariff_category: str = ""
    price_pence: int = 0
    price_pounds: Optional[float] = None
    pack_size: float = 28.0
    price_per_unit: Optional[float] = None
    date: str = ""
    concession: bool = False
    fetched_at: Optional[datetime] = None
    data_source: Optional[str] = None

    class Settings:
        name = "tariff_prices"
        indexes = ["product", "date", "tariff_category", "concession"]
