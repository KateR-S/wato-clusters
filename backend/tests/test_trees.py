import pytest


def test_list_trees_empty(client, headers):
    r = client.get("/trees", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


def test_create_tree(client, headers):
    r = client.post("/trees", json={"name": "Smith Family"}, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Smith Family"
    assert "id" in data


def test_get_tree(client, headers, tree):
    r = client.get(f"/trees/{tree.id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == tree.id


def test_get_tree_not_found(client, headers):
    r = client.get("/trees/9999", headers=headers)
    assert r.status_code == 404


def test_update_tree(client, headers, tree):
    r = client.put(f"/trees/{tree.id}", json={"name": "Updated"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"


def test_delete_tree(client, headers, tree):
    r = client.delete(f"/trees/{tree.id}", headers=headers)
    assert r.status_code == 204
    r2 = client.get(f"/trees/{tree.id}", headers=headers)
    assert r2.status_code == 404


def test_add_person(client, headers, tree):
    r = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Alice", "last_name": "Smith", "sex": "F"},
        headers=headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["first_name"] == "Alice"
    assert data["sex"] == "F"


def test_update_person(client, headers, tree):
    p = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Alice", "last_name": "Smith"},
        headers=headers,
    ).json()
    r = client.put(
        f"/trees/{tree.id}/people/{p['id']}",
        json={"first_name": "Alicia"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "Alicia"


def test_delete_person(client, headers, tree):
    p = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Bob", "last_name": "Jones"},
        headers=headers,
    ).json()
    r = client.delete(f"/trees/{tree.id}/people/{p['id']}", headers=headers)
    assert r.status_code == 204


def test_add_relationship(client, headers, tree):
    p1 = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Dad", "last_name": "S"},
        headers=headers,
    ).json()
    p2 = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Kid", "last_name": "S"},
        headers=headers,
    ).json()
    r = client.post(
        f"/trees/{tree.id}/relationships",
        json={"person1_id": p1["id"], "person2_id": p2["id"], "rel_type": "parent"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["rel_type"] == "parent"


def test_delete_relationship(client, headers, tree):
    p1 = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "A", "last_name": "B"},
        headers=headers,
    ).json()
    p2 = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "C", "last_name": "D"},
        headers=headers,
    ).json()
    rel = client.post(
        f"/trees/{tree.id}/relationships",
        json={"person1_id": p1["id"], "person2_id": p2["id"], "rel_type": "spouse"},
        headers=headers,
    ).json()
    r = client.delete(f"/trees/{tree.id}/relationships/{rel['id']}", headers=headers)
    assert r.status_code == 204


def test_tree_isolation_between_users(client, db, tree, headers):
    """A second user cannot access the first user's tree."""
    from tests.conftest import make_user, auth_headers
    user2 = make_user(db, email="user2@example.com")
    h2 = auth_headers(user2)
    r = client.get(f"/trees/{tree.id}", headers=h2)
    assert r.status_code == 403


def test_gedcom_upload(client, headers, tree):
    gedcom_content = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 1 JAN 1950
0 @I2@ INDI
1 NAME Jane /Doe/
1 SEX F
1 BIRT
2 DATE 15 MAR 1952
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
0 TRLR
"""
    r = client.post(
        f"/trees/{tree.id}/gedcom",
        files={"file": ("test.ged", gedcom_content.encode(), "text/plain")},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["people"]) == 2
    names = {p["first_name"] for p in data["people"]}
    assert "John" in names
    assert "Jane" in names
