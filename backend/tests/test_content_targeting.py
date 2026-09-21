import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.main import (
    Base,
    Reel,
    ReelCountry,
    User,
    UserCountryPreference,
    UserPreference,
    validate_category,
    validate_country_codes,
)


def test_country_validation_normalizes_and_deduplicates():
    assert validate_country_codes(["nl", "NL", "de"]) == ["NL", "DE"]


def test_country_validation_rejects_unknown_code():
    with pytest.raises(Exception):
        validate_country_codes(["ZZ"])


def test_category_validation_rejects_unknown_category():
    assert validate_category("SPORTS") == "sports"
    with pytest.raises(Exception):
        validate_category("unknown")


def test_country_and_category_targeting_query():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(email="test@example.invalid", onboarding_complete=True)
        session.add(user)
        session.flush()

        session.add(UserPreference(user_id=user.id, category="sports"))
        session.add_all([
            UserCountryPreference(user_id=user.id, country_code="NL"),
            UserCountryPreference(user_id=user.id, country_code="DE"),
        ])

        session.add_all([
            Reel(id="nl-sports", category="sports", video_url="https://cdn.invalid/nl.mp4", is_adult=False, published=True),
            Reel(id="us-sports", category="sports", video_url="https://cdn.invalid/us.mp4", is_adult=False, published=True),
            Reel(id="nl-music", category="music", video_url="https://cdn.invalid/music.mp4", is_adult=False, published=True),
            Reel(id="nl-adult", category="adult", video_url="https://cdn.invalid/adult.mp4", is_adult=True, published=True),
        ])
        session.flush()

        session.add_all([
            ReelCountry(reel_id="nl-sports", country_code="NL"),
            ReelCountry(reel_id="us-sports", country_code="US"),
            ReelCountry(reel_id="nl-music", country_code="NL"),
            ReelCountry(reel_id="nl-adult", country_code="NL"),
        ])
        session.commit()

        countries = ["NL", "DE"]
        statement = (
            select(Reel)
            .join(ReelCountry, ReelCountry.reel_id == Reel.id)
            .where(
                Reel.published.is_(True),
                ReelCountry.country_code.in_(countries),
                Reel.is_adult.is_(False),
                Reel.category == "sports",
            )
            .distinct()
            .order_by(Reel.id.asc())
        )
        rows = session.execute(statement).scalars().all()

        assert [row.id for row in rows] == ["nl-sports"]

    engine.dispose()
