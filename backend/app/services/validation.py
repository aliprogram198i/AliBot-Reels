from fastapi import HTTPException
from ..core.config import CATEGORIES,COUNTRY_CODES,MAX_COUNTRIES_PER_USER
def validate_country_codes(countries:list[str])->list[str]:
    normalized=list(dict.fromkeys(c.strip().upper() for c in countries))
    if not normalized or len(normalized)>MAX_COUNTRIES_PER_USER: raise HTTPException(422,"invalid country selection")
    if any(c not in COUNTRY_CODES for c in normalized): raise HTTPException(422,"unsupported country code")
    return normalized
def validate_category(category:str)->str:
    normalized=category.strip().lower()
    if normalized not in CATEGORIES: raise HTTPException(422,"unsupported content category")
    return normalized
