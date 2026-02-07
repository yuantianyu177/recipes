"""TDD Phase 2.1: Test health check and database connectivity."""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health endpoint should return 200 with status ok."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_database_connection(db_session):
    """Database connection should work and return 1."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_tables_created(db_session):
    """All expected tables should exist after migration."""
    result = await db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
    )
    tables = {row[0] for row in result.fetchall()}
    expected = {"recipes", "recipe_images", "ingredients", "recipe_ingredients", "tags", "recipe_tags"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
