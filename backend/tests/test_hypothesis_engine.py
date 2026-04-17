import pytest
from app.auth import hash_password
from app.hypothesis_engine import (
    generate_hypotheses,
    _cm_score,
    _birth_year_ok,
    _build_tree_generations,
    _pair_gen_dist_ok,
    _combo_consistent,
    Placement,
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
    rel_types = {p.relationship for p in top.placements}
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
                placement.relationship == "parent"
                and placement.tree_person_id == tp.id
                and placement.cluster_person_id == cp.id
            ), "Parent relationship should have been pruned by birth year constraint"


def test_all_match_pairs_in_hypothesis(db):
    """
    When multiple cluster persons each match multiple tree persons, every
    hypothesis must contain one placement per (cluster_person, tree_person)
    match pair — i.e. the full cross-product of matched pairs.
    """
    from app.auth import hash_password

    user = models.User(email="cross@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = models.Tree(user_id=user.id, name="Cross Tree")
    db.add(tree)
    db.flush()

    tp1 = models.Person(tree_id=tree.id, first_name="Tree", last_name="One", birth_year=1930, sex="M")
    tp2 = models.Person(tree_id=tree.id, first_name="Tree", last_name="Two", birth_year=1960, sex="F")
    db.add_all([tp1, tp2])
    db.flush()

    cluster = models.Cluster(user_id=user.id, name="Cross Cluster")
    db.add(cluster)
    db.flush()

    cp1 = models.ClusterPerson(cluster_id=cluster.id, name="Cluster One", birth_year=1958)
    cp2 = models.ClusterPerson(cluster_id=cluster.id, name="Cluster Two", birth_year=1962)
    db.add_all([cp1, cp2])
    db.flush()

    # cp1 matches both tp1 and tp2; cp2 matches both tp1 and tp2 → 4 match pairs
    for cp, (tp, cm) in [
        (cp1, (tp1, 889.0)),   # 1st_cousin range
        (cp1, (tp2, 889.0)),   # 1st_cousin range
        (cp2, (tp1, 889.0)),   # 1st_cousin range
        (cp2, (tp2, 889.0)),   # 1st_cousin range
    ]:
        db.add(models.Match(
            tree_id=tree.id, person_id=tp.id,
            cluster_person_id=cp.id, centimorgans=cm,
        ))
    db.commit()
    db.refresh(tree)
    db.refresh(cluster)

    hypotheses = generate_hypotheses(db, tree, cluster)
    assert len(hypotheses) > 0

    expected_pairs = {
        (cp1.id, tp1.id), (cp1.id, tp2.id),
        (cp2.id, tp1.id), (cp2.id, tp2.id),
    }
    for hyp in hypotheses:
        actual_pairs = {(p.cluster_person_id, p.tree_person_id) for p in hyp.placements}
        assert actual_pairs == expected_pairs, (
            f"Hypothesis placements {actual_pairs} != expected {expected_pairs}"
        )


def test_sibling_consistency_same_tree_person(db):
    """
    Two cluster half-siblings that both match the same tree person must be
    placed at the same generational distance from that tree person.
    A combo where one is 'great_grandparent' (gen +3) and the other is
    '1st_cousin' (gen 0) must be rejected.
    """
    from app.auth import hash_password
    import app.models as m

    # Build minimal model stubs via the DB to get real IDs
    user = m.User(email="sib@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = m.Tree(user_id=user.id, name="T")
    db.add(tree)
    db.flush()

    tp = m.Person(tree_id=tree.id, first_name="Shared", last_name="", birth_year=1930, sex="M")
    db.add(tp)
    db.flush()

    cluster = m.Cluster(user_id=user.id, name="C")
    db.add(cluster)
    db.flush()

    cp_a = m.ClusterPerson(cluster_id=cluster.id, name="Sibling A", birth_year=1970)
    cp_b = m.ClusterPerson(cluster_id=cluster.id, name="Sibling B", birth_year=1972)
    db.add_all([cp_a, cp_b])
    db.flush()

    rel = m.ClusterRelationship(
        cluster_id=cluster.id,
        person1_id=cp_a.id,
        person2_id=cp_b.id,
        rel_type="half_sibling",
    )
    db.add(rel)
    db.commit()

    # Inconsistent: great_grandparent (gen +3) vs 1st_cousin (gen 0) for same tree person
    placement_a = Placement(
        cluster_person_id=cp_a.id, cluster_person_name="Sibling A",
        tree_person_id=tp.id, tree_person_name="Shared",
        tree_person_birth_year=tp.birth_year,
        relationship_type="great_grandparent",
        centimorgans=400.0, cm_score=0.5,
    )
    placement_b = Placement(
        cluster_person_id=cp_b.id, cluster_person_name="Sibling B",
        tree_person_id=tp.id, tree_person_name="Shared",
        tree_person_birth_year=tp.birth_year,
        relationship_type="1st_cousin",
        centimorgans=850.0, cm_score=0.8,
    )
    assert not _combo_consistent((placement_a, placement_b), [rel]), (
        "Same-tree-person combo with gen dist +3 vs 0 for half-siblings must be rejected"
    )

    # Consistent: both are '1st_cousin' (gen 0) of the same tree person
    placement_a_ok = Placement(
        cluster_person_id=cp_a.id, cluster_person_name="Sibling A",
        tree_person_id=tp.id, tree_person_name="Shared",
        tree_person_birth_year=tp.birth_year,
        relationship_type="1st_cousin",
        centimorgans=900.0, cm_score=0.9,
    )
    placement_b_ok = Placement(
        cluster_person_id=cp_b.id, cluster_person_name="Sibling B",
        tree_person_id=tp.id, tree_person_name="Shared",
        tree_person_birth_year=tp.birth_year,
        relationship_type="1st_cousin",
        centimorgans=850.0, cm_score=0.8,
    )
    assert _combo_consistent((placement_a_ok, placement_b_ok), [rel]), (
        "Same-tree-person combo with equal gen dist for half-siblings must be accepted"
    )


def test_half_sibling_removed_rel_same_tree_person_rejected(db):
    """
    Half-siblings (same generation, c_delta=0) matching the same tree person
    must both be assigned relationship types with the same generational
    distance.  1st_cousin_1r (d=±1) paired with half_1st_cousin (d=0) must be
    rejected because no d1 in {1,-1} and d2 in {0} satisfies d1-d2=0.
    """
    user = models.User(email="removed@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = models.Tree(user_id=user.id, name="T")
    db.add(tree)
    db.flush()

    tp = models.Person(tree_id=tree.id, first_name="Tree", last_name="Person",
                       birth_year=1950, sex="M")
    db.add(tp)
    db.flush()

    cluster = models.Cluster(user_id=user.id, name="C")
    db.add(cluster)
    db.flush()

    cp_a = models.ClusterPerson(cluster_id=cluster.id, name="Half Sib A", birth_year=1975)
    cp_b = models.ClusterPerson(cluster_id=cluster.id, name="Half Sib B", birth_year=1977)
    db.add_all([cp_a, cp_b])
    db.flush()

    rel = models.ClusterRelationship(
        cluster_id=cluster.id,
        person1_id=cp_a.id,
        person2_id=cp_b.id,
        rel_type="half_sibling",
    )
    db.add(rel)
    db.commit()

    p_a_1r = Placement(
        cluster_person_id=cp_a.id, cluster_person_name="Half Sib A",
        tree_person_id=tp.id, tree_person_name="Tree Person",
        tree_person_birth_year=1950,
        relationship_type="1st_cousin_1r",  # d ∈ {+1, -1}
        centimorgans=460.0, cm_score=0.7,
    )
    p_b_half = Placement(
        cluster_person_id=cp_b.id, cluster_person_name="Half Sib B",
        tree_person_id=tp.id, tree_person_name="Tree Person",
        tree_person_birth_year=1950,
        relationship_type="half_1st_cousin",  # d = 0
        centimorgans=200.0, cm_score=0.6,
    )
    assert not _combo_consistent((p_a_1r, p_b_half), [rel]), (
        "half_sibling pair with 1st_cousin_1r vs half_1st_cousin to same tree person must be rejected"
    )

    # Consistent: both 1st_cousin_1r (d=±1), same ambiguous set → d1-d2=0 is satisfiable
    p_b_1r = Placement(
        cluster_person_id=cp_b.id, cluster_person_name="Half Sib B",
        tree_person_id=tp.id, tree_person_name="Tree Person",
        tree_person_birth_year=1950,
        relationship_type="1st_cousin_1r",  # d ∈ {+1, -1}
        centimorgans=300.0, cm_score=0.6,
    )
    assert _combo_consistent((p_a_1r, p_b_1r), [rel]), (
        "half_sibling pair both with 1st_cousin_1r to same tree person must be accepted"
    )


def test_cm_score_soft_extension():
    """Values just outside the standard range get a small but positive score."""
    lo, hi = CM_RANGES["1st_cousin_1r"]  # 141, 851
    half_width = (hi - lo) / 2           # 355
    midpoint = (lo + hi) / 2             # 496

    # Value inside range: normal score
    assert _cm_score(midpoint, "1st_cousin_1r") == 1.0

    # Value just below lower boundary (in soft zone): tiny positive score
    cm_soft = lo - half_width * 0.1  # ~105 cM
    score_soft = _cm_score(cm_soft, "1st_cousin_1r")
    assert score_soft > 0.0, "Value in soft zone below lo should have tiny positive score"
    assert score_soft < 0.05, "Soft-zone score must be < 0.05"

    # Value well outside soft zone: must be 0
    cm_far = lo - half_width * 0.5  # well beyond soft limit
    assert _cm_score(cm_far, "1st_cousin_1r") == 0.0


def test_half_sibling_same_gen_diff_rel_type_rejected(db):
    """
    Half-siblings to the same tree person must have the EXACT same relationship
    type, not merely the same generational distance.

    1st_cousin (d=0) paired with half_1st_cousin (d=0) must be rejected even
    though both have generational distance 0.  Likewise 1st_cousin vs
    2nd_cousin (both d=0).  Only same-type pairs (e.g. both 1st_cousin) are
    accepted.
    """
    user = models.User(email="samedtype@test.com",
                       hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = models.Tree(user_id=user.id, name="T")
    db.add(tree)
    db.flush()

    tp = models.Person(tree_id=tree.id, first_name="Shared", last_name="Person",
                       birth_year=1947, sex="M")
    db.add(tp)
    db.flush()

    cluster = models.Cluster(user_id=user.id, name="C")
    db.add(cluster)
    db.flush()

    cp_a = models.ClusterPerson(cluster_id=cluster.id, name="Will", birth_year=1975)
    cp_b = models.ClusterPerson(cluster_id=cluster.id, name="Hayleigh", birth_year=1965)
    db.add_all([cp_a, cp_b])
    db.flush()

    rel = models.ClusterRelationship(
        cluster_id=cluster.id,
        person1_id=cp_a.id,
        person2_id=cp_b.id,
        rel_type="half_sibling",
    )
    db.add(rel)
    db.commit()

    # Bad: 1st_cousin (d=0) vs half_1st_cousin (d=0) — different types, same d
    p_a_1c = Placement(cp_a.id, "Will", tp.id, "Shared Person", 1947,
                       "1st_cousin", 1009.0, 0.8)
    p_b_half = Placement(cp_b.id, "Hayleigh", tp.id, "Shared Person", 1947,
                         "half_1st_cousin", 583.0, 0.6)
    assert not _combo_consistent((p_a_1c, p_b_half), [rel]), (
        "half_sibling pair: 1st_cousin vs half_1st_cousin (same d=0) to same "
        "tree person must be rejected"
    )

    # Bad: 1st_cousin (d=0) vs 2nd_cousin (d=0) — different types, same d
    p_b_2c = Placement(cp_b.id, "Hayleigh", tp.id, "Shared Person", 1947,
                       "2nd_cousin", 583.0, 0.6)
    assert not _combo_consistent((p_a_1c, p_b_2c), [rel]), (
        "half_sibling pair: 1st_cousin vs 2nd_cousin (same d=0) to same "
        "tree person must be rejected"
    )

    # Good: both 1st_cousin (same type, same d)
    p_b_1c = Placement(cp_b.id, "Hayleigh", tp.id, "Shared Person", 1947,
                       "1st_cousin", 583.0, 0.7)
    assert _combo_consistent((p_a_1c, p_b_1c), [rel]), (
        "half_sibling pair: both 1st_cousin to same tree person must be accepted"
    )


def test_tree_relative_consistency_same_gen(db):
    """
    When a cluster person matches two tree persons who are same-generation
    siblings, both relationships must have the same generational distance.
    Pairing 1st_cousin (d=0) to T1 with 1st_cousin_1r (d=±1) to T2 must be
    rejected; pairing 1st_cousin with 1st_cousin must be accepted.
    """
    user = models.User(email="treerel@test.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.flush()

    tree = models.Tree(user_id=user.id, name="T")
    db.add(tree)
    db.flush()

    tp1 = models.Person(tree_id=tree.id, first_name="Sibling", last_name="A",
                        birth_year=1960, sex="M")
    tp2 = models.Person(tree_id=tree.id, first_name="Sibling", last_name="B",
                        birth_year=1962, sex="F")
    db.add_all([tp1, tp2])
    db.flush()

    tree_rel = models.Relationship(
        tree_id=tree.id,
        person1_id=tp1.id,
        person2_id=tp2.id,
        rel_type="full_sibling",
    )
    db.add(tree_rel)
    db.flush()

    cluster = models.Cluster(user_id=user.id, name="C")
    db.add(cluster)
    db.flush()

    cp = models.ClusterPerson(cluster_id=cluster.id, name="Unknown", birth_year=1985)
    db.add(cp)
    db.commit()

    tree_gen = _build_tree_generations([tree_rel], {tp1.id, tp2.id})

    p_t1 = Placement(
        cluster_person_id=cp.id, cluster_person_name="Unknown",
        tree_person_id=tp1.id, tree_person_name="Sibling A",
        tree_person_birth_year=1960,
        relationship_type="1st_cousin",  # d = 0
        centimorgans=889.0, cm_score=0.9,
    )
    p_t2_bad = Placement(
        cluster_person_id=cp.id, cluster_person_name="Unknown",
        tree_person_id=tp2.id, tree_person_name="Sibling B",
        tree_person_birth_year=1962,
        relationship_type="1st_cousin_1r",  # d ∈ {+1, -1}; 0 not in set
        centimorgans=600.0, cm_score=0.7,
    )
    assert not _combo_consistent((p_t1, p_t2_bad), [], tree_gen), (
        "1st_cousin to T1 and 1st_cousin_1r to same-gen T2 must be rejected"
    )

    p_t2_ok = Placement(
        cluster_person_id=cp.id, cluster_person_name="Unknown",
        tree_person_id=tp2.id, tree_person_name="Sibling B",
        tree_person_birth_year=1962,
        relationship_type="1st_cousin",  # d = 0
        centimorgans=600.0, cm_score=0.7,
    )
    assert _combo_consistent((p_t1, p_t2_ok), [], tree_gen), (
        "1st_cousin to both same-gen tree persons must be accepted"
    )

