from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DiscoveryHealthResponse(BaseModel):
    brand_id: int
    configured_queries: int
    successful_query_runs: int
    failed_query_runs: int
    discovered_results: int
    unique_domains: int
    last_successful_discovery: Optional[datetime] = None
