import pytest
from tests.conftest import make_user, auth_headers


def test_register(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "pw123"})
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pw"})
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "pw"})
    assert r.status_code == 400


def test_login(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pw123"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "pw123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pw123"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_endpoint_no_token(client):
    r = client.get("/trees")
    assert r.status_code == 401


def test_protected_endpoint_bad_token(client):
    r = client.get("/trees", headers={"Authorization": "Bearer bad.token.here"})
    assert r.status_code == 401
