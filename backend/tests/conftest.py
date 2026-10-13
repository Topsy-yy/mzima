"""Shared pytest fixtures."""
import os

import pytest

# Point settings at the test env file before any app imports
os.environ.setdefault("ENV_FILE", ".env.test")


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear the lru_cache between tests so env changes take effect."""
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
