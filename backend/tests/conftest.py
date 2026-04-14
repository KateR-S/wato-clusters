"""
Shared test fixtures.
Uses an in-memory SQLite database; each test gets a fresh DB.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models
from app.auth import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"


def _make_engine():
    # StaticPool ensures all connections share the same in-memory database
    eng = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def set_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return eng


@pytest.fixture()
def db():
    """Provide a fresh in-memory DB session for each test."""
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def client(db):
    """FastAPI TestClient with DB overridden to in-memory."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(db, email="test@example.com", password="secret"):
    user = models.User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: models.User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user(db):
    return make_user(db)


@pytest.fixture()
def headers(user):
    return auth_headers(user)


@pytest.fixture()
def tree(db, user):
    t = models.Tree(user_id=user.id, name="My Tree")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def cluster(db, user):
    c = models.Cluster(user_id=user.id, name="Unknown Cluster")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
