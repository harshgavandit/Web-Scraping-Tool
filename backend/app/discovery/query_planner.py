from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class GoogleQuerySpec:
    category: str
    query: str
    product: Optional[str] = None
    competitor: Optional[str] = None


def _unique(values: List[str]) -> List[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def build_google_query_specs(
    brand_name: str,
    keywords: List[str],
    competitors: List[str],
) -> List[GoogleQuerySpec]:
    """Build an auditable portfolio of focused Google web-discovery queries."""
    brand = brand_name.strip()
    specs = [
        GoogleQuerySpec("brand_presence", f'"{brand}" (brand OR products OR company)'),
        GoogleQuerySpec("customer_feedback", f'"{brand}" (review OR complaint OR "customer feedback" OR comfort OR quality)'),
        GoogleQuerySpec("reputation_risk", f'"{brand}" (controversy OR recall OR lawsuit OR boycott OR defect OR complaint)'),
        GoogleQuerySpec("viral_trending", f'"{brand}" (viral OR trending OR campaign OR "social media")'),
        GoogleQuerySpec("articles_blogs", f'"{brand}" (article OR analysis OR blog OR review)'),
    ]

    seen = {brand.casefold()}
    for keyword in _unique(keywords):
        if keyword.casefold() in seen:
            continue
        seen.add(keyword.casefold())
        specs.extend([
            GoogleQuerySpec(
                "product_review",
                f'"{brand}" "{keyword}" (review OR rating OR "pros and cons" OR feedback)',
                product=keyword,
            ),
            GoogleQuerySpec(
                "product_complaint",
                f'"{brand}" "{keyword}" (complaint OR problem OR uncomfortable OR durability OR overpriced)',
                product=keyword,
            ),
        ])
        if len(seen) >= 9:
            break

    for competitor in _unique(competitors)[:6]:
        specs.append(GoogleQuerySpec(
            "competitor_comparison",
            f'"{brand}" "{competitor}" (versus OR vs OR comparison OR compared OR review)',
            competitor=competitor,
        ))

    return specs
