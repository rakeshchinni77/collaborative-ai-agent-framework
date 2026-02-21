import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# =========================================================
# Ensure pytest uses SQLite (not Postgres)
# =========================================================
os.environ["PYTEST_RUNNING"] = "1"

# =========================================================
# Add project root to Python path so `import src` works
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

# =========================================================
# Now imports work
# =========================================================
from src.main import app
from src.database import Base, engine

# =========================================================
# Create in-memory test DB
# =========================================================
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# =========================================================
# Test client
# =========================================================
@pytest.fixture(scope="session")
def client():
    return TestClient(app)

# =========================================================
# Utility UUID fixture
# =========================================================
@pytest.fixture
def valid_uuid():
    return str(uuid.uuid4())