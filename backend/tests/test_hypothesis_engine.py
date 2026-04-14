import pytest
from app.hypothesis_engine import (
    generate_hypotheses,
    _cm_score,
    _birth_year_ok,
    CM_RANGES,
)
from app import models


def test_cm_score_within_range():
    lo, hi = CM_RANGES["1st_cousin"]
    mid = (lo + hi) / 2
    score = _cm_score(mid, "1st_cousin")
    assert score == 1.0


def test_cm_score_outside_range():
    score = _cm_score(0.0, "parent")  # parent range is 2376-3720
    assert score == 0.0


def test_cm_score_at_boundary():
    lo, hi = CM_RANGES["1st_cousin"]
    assert _cm_score(lo, "1st_cousin") == 0.0
    assert _cm_score(hi, "1st_cousin") == 0.0


def test_cm_score_unknown_relationship():
    assert _cm_score(500.0, "nonexistent_rel") == 0.0


def test_birth_year_parent_valid():
    # Parent born 1950, child born 1975 → difference = 25 >= 14
    assert _birth_year_ok(1950, 1975, "parent") is True


def test_birth_year_parent_invalid():
    # Parent born 1960, child born 1965 → difference = 5 < 14
    assert _birth_year_ok(1960, 1965, "parent") is False


def test_birth_year_child_valid():
    # Person born 1975 is child → relative (parent) born 1950 → 1975-1950=25 >= 14
    assert _birth_year_ok(1975, 1950, "child") is True


def test_birth_year_child_invalid():
    # Person born 1965 is child, relative born 1960 → 1965-1960=5 < 14
    assert _birth_year_ok(1965, 1960, "child") is False


def test_birth_year_missing_data():
    # Missing birth years → cannot rule out, return True
    assert _birth_year_ok(None, 1980, "parent") is True
    assert _birth_year_ok(1950, None, "parent") is True
    assert _birth_year_ok(None, None, "parent") is True


def test_generate_hypotheses_basic(db):
    """End-to-end test of the hypothesis engine with known-answer scenario."""
    # Create user
    from app.auth import hash_password
    user = models.User(email="hyp@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    # Create tree with one person
    tree = models.Tree(user_id=user.id, name="Test Tree")
    db.add(tree)
    db.flush()

    tp = models.Person(
        tree_id=tree.id,
        first_name="Known",
        last_name="Person",
        birth_year=1960,
        sex="M",
    )
    db.add(tp)
    db.flush()

    # Create cluster with one person
    cluster = models.Cluster(user_id=user.id, name="Test Cluster")
    db.add(cluster)
    db.flush()

    cp = models.ClusterPerson(
        cluster_id=cluster.id,
        name="Unknown Person",
        birth_year=1958,
    )
    db.add(cp)
    db.flush()

    # Add a match in the 1st_cousin range (553-1225)
    match = models.Match(
        tree_id=tree.id,
        person_id=tp.id,
        cluster_person_id=cp.id,
        centimorgans=889.0,
    )
    db.add(match)
    db.commit()

    # Reload with relationships
    db.refresh(tree)
    db.refresh(cluster)

    hypotheses = generate_hypotheses(db, tree, cluster)
    assert len(hypotheses) > 0

    # Best hypothesis should include 1st_cousin
    top = hypotheses[0]
    rel_types = {p.relationship_type for p in top.placements}
    assert "1st_cousin" in rel_types


def test_generate_hypotheses_no_matches(db):
    from app.auth import hash_password
    user = models.User(email="nomat@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = models.Tree(user_id=user.id, name="Tree")
    db.add(tree)
    cluster = models.Cluster(user_id=user.id, name="Cluster")
    db.add(cluster)
    db.commit()
    db.refresh(tree)
    db.refresh(cluster)

    result = generate_hypotheses(db, tree, cluster)
    assert result == []


def test_generate_hypotheses_birth_year_prunes_parent(db):
    """
    If tree person was born in 1990 and cluster person in 1989,
    'parent' (tp is parent of cp) should be pruned because 1989-1990=-1 < 14.
    """
    from app.auth import hash_password
    user = models.User(email="prune@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = models.Tree(user_id=user.id, name="Tree")
    db.add(tree)
    db.flush()

    tp = models.Person(
        tree_id=tree.id, first_name="Young", last_name="Person",
        birth_year=1990, sex="M"
    )
    db.add(tp)
    db.flush()

    cluster = models.Cluster(user_id=user.id, name="Cluster")
    db.add(cluster)
    db.flush()

    cp = models.ClusterPerson(
        cluster_id=cluster.id, name="Older Unknown", birth_year=1989
    )
    db.add(cp)
    db.flush()

    match = models.Match(
        tree_id=tree.id, person_id=tp.id,
        cluster_person_id=cp.id, centimorgans=3000.0
    )
    db.add(match)
    db.commit()
    db.refresh(tree)
    db.refresh(cluster)

    hypotheses = generate_hypotheses(db, tree, cluster)
    for hyp in hypotheses:
        for placement in hyp.placements:
            assert not (
                placement.relationship_type == "parent"
                and placement.tree_person_id == tp.id
                and placement.cluster_person_id == cp.id
            ), "Parent relationship should have been pruned by birth year constraint"
