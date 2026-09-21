import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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


@pytest.mark.asyncio
async def test_country_and_category_targeting_query():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        user = User(email="test@example.invalid", onboarding_complete=True)
        session.add(user)
        await session.flush()

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
        await session.flush()

        session.add_all([
            ReelCountry(reel_id="nl-sports", country_code="NL"),
            ReelCountry(reel_id="us-sports", country_code="US"),
            ReelCountry(reel_id="nl-music", country_code="NL"),
            ReelCountry(reel_id="nl-adult", country_code="NL"),
        ])
        await session.commit()

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
        rows = (await session.execute(statement)).scalars().all()

        assert [row.id for row in rows] == ["nl-sports"]

    await engine.dispose()
