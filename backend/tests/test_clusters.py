import pytest


def test_list_clusters_empty(client, headers):
    r = client.get("/clusters", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


def test_create_cluster(client, headers):
    r = client.post("/clusters", json={"name": "Unknown Group"}, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Unknown Group"


def test_get_cluster(client, headers, cluster):
    r = client.get(f"/clusters/{cluster.id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == cluster.id


def test_delete_cluster(client, headers, cluster):
    r = client.delete(f"/clusters/{cluster.id}", headers=headers)
    assert r.status_code == 204
    r2 = client.get(f"/clusters/{cluster.id}", headers=headers)
    assert r2.status_code == 404


def test_add_cluster_person(client, headers, cluster):
    r = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Unknown Alice", "birth_year": 1980},
        headers=headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Unknown Alice"
    assert data["birth_year"] == 1980


def test_update_cluster_person(client, headers, cluster):
    cp = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Unknown Bob"},
        headers=headers,
    ).json()
    r = client.put(
        f"/clusters/{cluster.id}/people/{cp['id']}",
        json={"name": "Bob Updated", "birth_year": 1975},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Bob Updated"
    assert data["birth_year"] == 1975


def test_delete_cluster_person(client, headers, cluster):
    cp = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "To Delete"},
        headers=headers,
    ).json()
    r = client.delete(f"/clusters/{cluster.id}/people/{cp['id']}", headers=headers)
    assert r.status_code == 204


def test_add_cluster_relationship(client, headers, cluster):
    cp1 = client.post(
        f"/clusters/{cluster.id}/people", json={"name": "P1"}, headers=headers
    ).json()
    cp2 = client.post(
        f"/clusters/{cluster.id}/people", json={"name": "P2"}, headers=headers
    ).json()
    r = client.post(
        f"/clusters/{cluster.id}/relationships",
        json={"person1_id": cp1["id"], "person2_id": cp2["id"], "rel_type": "full_sibling"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["rel_type"] == "full_sibling"


def test_delete_cluster_relationship(client, headers, cluster):
    cp1 = client.post(
        f"/clusters/{cluster.id}/people", json={"name": "P1"}, headers=headers
    ).json()
    cp2 = client.post(
        f"/clusters/{cluster.id}/people", json={"name": "P2"}, headers=headers
    ).json()
    rel = client.post(
        f"/clusters/{cluster.id}/relationships",
        json={"person1_id": cp1["id"], "person2_id": cp2["id"], "rel_type": "spouse"},
        headers=headers,
    ).json()
    r = client.delete(f"/clusters/{cluster.id}/relationships/{rel['id']}", headers=headers)
    assert r.status_code == 204


def test_cluster_isolation_between_users(client, db, cluster, headers):
    from tests.conftest import make_user, auth_headers
    user2 = make_user(db, email="user2@example.com")
    h2 = auth_headers(user2)
    r = client.get(f"/clusters/{cluster.id}", headers=h2)
    assert r.status_code == 403
