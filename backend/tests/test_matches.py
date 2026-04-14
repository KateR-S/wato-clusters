import pytest


def _setup_match_fixtures(client, headers, tree, cluster):
    """Helper: creates one tree person and one cluster person, returns their IDs."""
    person = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Alice", "last_name": "Smith"},
        headers=headers,
    ).json()
    cp = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Unknown X"},
        headers=headers,
    ).json()
    return person["id"], cp["id"]


def test_list_matches_empty(client, headers, tree):
    r = client.get(f"/trees/{tree.id}/matches", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


def test_add_match(client, headers, tree, cluster):
    person_id, cp_id = _setup_match_fixtures(client, headers, tree, cluster)
    r = client.post(
        f"/trees/{tree.id}/matches",
        json={"person_id": person_id, "cluster_person_id": cp_id, "centimorgans": 850.0},
        headers=headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["centimorgans"] == 850.0
    assert data["person_id"] == person_id
    assert data["cluster_person_id"] == cp_id


def test_delete_match(client, headers, tree, cluster):
    person_id, cp_id = _setup_match_fixtures(client, headers, tree, cluster)
    match = client.post(
        f"/trees/{tree.id}/matches",
        json={"person_id": person_id, "cluster_person_id": cp_id, "centimorgans": 200.0},
        headers=headers,
    ).json()
    r = client.delete(f"/trees/{tree.id}/matches/{match['id']}", headers=headers)
    assert r.status_code == 204


def test_match_invalid_person(client, headers, tree, cluster):
    cp = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Unknown Y"},
        headers=headers,
    ).json()
    r = client.post(
        f"/trees/{tree.id}/matches",
        json={"person_id": 9999, "cluster_person_id": cp["id"], "centimorgans": 500.0},
        headers=headers,
    )
    assert r.status_code == 404


def test_match_invalid_cluster_person(client, headers, tree):
    person = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Bob", "last_name": "Jones"},
        headers=headers,
    ).json()
    r = client.post(
        f"/trees/{tree.id}/matches",
        json={"person_id": person["id"], "cluster_person_id": 9999, "centimorgans": 500.0},
        headers=headers,
    )
    assert r.status_code == 404
