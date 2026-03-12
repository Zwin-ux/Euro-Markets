from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PositionInput(BaseModel):
    position_id: str = Field(..., description="Unique identifier for the position")
    position_name: str = Field(..., description="Display name for the position")
    currency: str = Field(..., description="Position currency, e.g. USD")
    market_value_local: float = Field(..., description="Market value expressed in the local currency")
    asset_class: str = Field(default="", description="Optional asset class label")
    book: str = Field(default="", description="Optional book or desk label")


class PortfolioAnalysisRequest(BaseModel):
    positions: list[PositionInput]
    lookback_days: int = Field(default=252, ge=30, le=730)
    confidence_level: float = Field(default=0.95, gt=0, lt=1)
    rolling_window: int = Field(default=20, ge=2, le=180)
    frequency: Literal["D", "M", "Q", "A"] = "D"
    scenario_shocks: dict[str, float] = Field(default_factory=dict)
