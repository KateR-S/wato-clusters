import pytest


def _setup_hypothesis_fixtures(client, headers, tree, cluster):
    """
    Creates a tree person (birth 1960) and two cluster people.
    Adds a cM match for 1st-cousin range (~850 cM) so hypotheses can be generated.
    Returns (tree_person, cp1, cp2).
    """
    tp = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Known", "last_name": "Person", "birth_year": 1960, "sex": "M"},
        headers=headers,
    ).json()

    cp1 = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Unknown A", "birth_year": 1958},
        headers=headers,
    ).json()

    cp2 = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Unknown B", "birth_year": 1985},
        headers=headers,
    ).json()

    # Add sibling relationship in cluster
    client.post(
        f"/clusters/{cluster.id}/relationships",
        json={"person1_id": cp1["id"], "person2_id": cp2["id"], "rel_type": "full_sibling"},
        headers=headers,
    )

    # Match cp1 to tree person with ~850 cM (1st_cousin range: 553-1225)
    client.post(
        f"/trees/{tree.id}/matches",
        json={"person_id": tp["id"], "cluster_person_id": cp1["id"], "centimorgans": 850.0},
        headers=headers,
    )

    return tp, cp1, cp2


def test_generate_hypotheses(client, headers, tree, cluster):
    tp, cp1, _cp2 = _setup_hypothesis_fixtures(client, headers, tree, cluster)
    r = client.post(
        f"/trees/{tree.id}/hypotheses",
        json={"cluster_id": cluster.id},
        headers=headers,
    )
    assert r.status_code == 200
    hypotheses = r.json()
    assert isinstance(hypotheses, list)
    assert len(hypotheses) > 0
    # Each hypothesis should have a score and placements
    h = hypotheses[0]
    assert "rank" in h
    assert "score" in h
    assert "likelihood_percent" in h
    assert "placements" in h
    assert h["rank"] == 1
    assert h["score"] > 0
    # Best hypothesis should contain the cluster person with a cM match
    cp_ids = [p["cluster_person_id"] for p in h["placements"]]
    assert cp1["id"] in cp_ids


def test_hypotheses_score_ordering(client, headers, tree, cluster):
    """Hypotheses should be returned sorted by score descending."""
    _setup_hypothesis_fixtures(client, headers, tree, cluster)
    r = client.post(
        f"/trees/{tree.id}/hypotheses",
        json={"cluster_id": cluster.id},
        headers=headers,
    )
    hypotheses = r.json()
    scores = [h["score"] for h in hypotheses]
    assert scores == sorted(scores, reverse=True)


def test_hypotheses_no_matches_returns_empty(client, headers, tree, cluster):
    r = client.post(
        f"/trees/{tree.id}/hypotheses",
        json={"cluster_id": cluster.id},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json() == []


def test_hypotheses_wrong_tree_returns_403(client, db, tree, cluster, headers):
    from tests.conftest import make_user, auth_headers
    user2 = make_user(db, email="other@example.com")
    h2 = auth_headers(user2)
    r = client.post(
        f"/trees/{tree.id}/hypotheses",
        json={"cluster_id": cluster.id},
        headers=h2,
    )
    assert r.status_code == 403


def test_birth_year_constraint_respected(client, headers, tree, cluster):
    """
    A tree person born in 1990 cannot be the parent of a cluster person born in 1989.
    Hypotheses with 'parent' relationship in that direction should be pruned.
    """
    # Tree person born 1990
    tp = client.post(
        f"/trees/{tree.id}/people",
        json={"first_name": "Young", "last_name": "Person", "birth_year": 1990},
        headers=headers,
    ).json()

    # Cluster person born 1989 (one year OLDER than tree person)
    cp = client.post(
        f"/clusters/{cluster.id}/people",
        json={"name": "Older Unknown", "birth_year": 1989},
        headers=headers,
    ).json()

    # Match with cM in parent range (3000 cM)
    client.post(
        f"/trees/{tree.id}/matches",
        json={"person_id": tp["id"], "cluster_person_id": cp["id"], "centimorgans": 3000.0},
        headers=headers,
    )

    r = client.post(
        f"/trees/{tree.id}/hypotheses",
        json={"cluster_id": cluster.id},
        headers=headers,
    )
    assert r.status_code == 200
    hypotheses = r.json()

    # No hypothesis should suggest tree person is parent of cluster person born before them
    for hyp in hypotheses:
        for placement in hyp["placements"]:
            if placement["tree_person_id"] == tp["id"] and placement["cluster_person_id"] == cp["id"]:
                if placement["relationship"] == "parent":
                    # parent means tp is parent of cp: tp birth (1990) must be >= 14 before cp birth (1989)
                    # 1989 - 1990 = -1, which is < 14, so this should NOT appear
                    pytest.fail(
                        f"Invalid 'parent' hypothesis found: tree person born 1990 "
                        f"cannot parent cluster person born 1989"
                    )
