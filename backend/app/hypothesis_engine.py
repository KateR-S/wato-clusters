"""
Hypothesis engine for DNA genealogy analysis.

Given a main family tree and a floating cluster with cM matches, generates
ranked hypotheses for how cluster people could fit into the main tree.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import product
from typing import Optional

from sqlalchemy.orm import Session

from . import models
from .schemas import HypothesisOut, PlacementEntry

# cM ranges per relationship type (min, max) from ISOGG
CM_RANGES: dict[str, tuple[float, float]] = {
    "parent": (2376, 3720),
    "child": (2376, 3720),
    "full_sibling": (1613, 3488),
    "grandparent": (984, 2311),
    "grandchild": (984, 2311),
    "aunt_uncle": (1156, 2311),
    "niece_nephew": (1156, 2311),
    "half_sibling": (1160, 2650),
    "1st_cousin": (553, 1225),
    "half_aunt_uncle": (500, 1446),
    "half_niece_nephew": (500, 1446),
    "great_grandparent": (0, 841),
    "great_grandchild": (0, 841),
    "1st_cousin_1r": (141, 851),
    "2nd_cousin": (46, 515),
    "1st_cousin_2r": (43, 531),
    "2nd_cousin_1r": (0, 311),
    "3rd_cousin": (0, 173),
    "half_1st_cousin": (0, 449),
}

# Generational distance: how many generations OLDER the tree person is
# relative to the cluster person. Positive = tree person is older.
# None = ambiguous (e.g., cousin-once-removed can be older or younger branch).
GEN_DIST: dict[str, Optional[int]] = {
    "parent": 1,
    "child": -1,
    "full_sibling": 0,
    "half_sibling": 0,
    "grandparent": 2,
    "grandchild": -2,
    "aunt_uncle": 1,
    "niece_nephew": -1,
    "half_aunt_uncle": 1,
    "half_niece_nephew": -1,
    "great_grandparent": 3,
    "great_grandchild": -3,
    "1st_cousin": 0,
    "half_1st_cousin": 0,
    "1st_cousin_1r": None,   # ambiguous: older or younger branch
    "2nd_cousin": 0,
    "1st_cousin_2r": None,   # ambiguous
    "2nd_cousin_1r": None,   # ambiguous
    "3rd_cousin": 0,
}

# Generational delta for cluster relationships: how many generations older
# person1 is relative to person2 in the cluster. Positive = person1 is older.
CLUSTER_GEN_DELTA: dict[str, int] = {
    "parent": 1,
    "child": -1,
    "full_sibling": 0,
    "half_sibling": 0,
    "half_parent": 1,
    "half_child": -1,
    "spouse": 0,
}

AVG_GEN_YEARS = 25       # average years per generation
GEN_BIRTH_TOLERANCE = 1.5  # allow ±1.5 generation tolerance in birth year checks

MIN_PARENT_AGE = 14


@dataclass
class Placement:
    """A single cluster_person → {tree_person, relationship} assignment."""
    cluster_person_id: int
    cluster_person_name: str
    tree_person_id: int
    tree_person_name: str
    tree_person_birth_year: Optional[int]
    relationship_type: str
    centimorgans: float
    cm_score: float  # 0-1, how central the cM is to the expected range


def _cm_score(cm: float, rel_type: str) -> float:
    """Return a 0-1 score for how well a cM value fits a relationship type."""
    if rel_type not in CM_RANGES:
        return 0.0
    lo, hi = CM_RANGES[rel_type]
    if cm < lo or cm > hi:
        return 0.0
    if lo == hi:
        return 1.0
    midpoint = (lo + hi) / 2
    half_width = (hi - lo) / 2
    # Gaussian-like: 1 at midpoint, 0 at edges
    distance = abs(cm - midpoint) / half_width
    return max(0.0, 1.0 - distance)


def _birth_year_ok(
    person_birth: Optional[int],
    relative_birth: Optional[int],
    rel_type: str,
) -> bool:
    """
    Return False if the birth years violate parent-age constraints.
    Only checks when both birth years are known.
    """
    if person_birth is None or relative_birth is None:
        return True  # cannot rule out when data is missing

    if rel_type == "parent":
        # person is the parent of relative → person must be ≥14 years older
        return (relative_birth - person_birth) >= MIN_PARENT_AGE
    if rel_type == "child":
        # person is the child → relative must be ≥14 years older
        return (person_birth - relative_birth) >= MIN_PARENT_AGE
    if rel_type in ("half_parent",):
        return (relative_birth - person_birth) >= MIN_PARENT_AGE
    if rel_type in ("half_child",):
        return (person_birth - relative_birth) >= MIN_PARENT_AGE
    if rel_type == "grandparent":
        return (relative_birth - person_birth) >= MIN_PARENT_AGE * 2
    if rel_type == "grandchild":
        return (person_birth - relative_birth) >= MIN_PARENT_AGE * 2
    return True


def generate_hypotheses(
    db: Session,
    tree: models.Tree,
    cluster: models.Cluster,
) -> list[HypothesisOut]:
    """
    Generate ranked placement hypotheses for a cluster onto a tree.

    Strategy
    --------
    For each cluster person that has at least one cM match to a tree person:
      - enumerate every (tree_person, relationship_type) pair whose cM range
        contains the observed cM value and whose birth years are compatible.

    A *hypothesis* is a consistent assignment of one placement per cluster
    person (all cluster members that have matches must be placed).  Consistency
    means the inter-cluster relationships are respected: if cluster person A is
    the parent of cluster person B, then the tree placements for A and B must
    reflect that generational ordering.  For every cluster relationship between
    two placed persons, we compute the expected generational difference between
    their respective tree-person matches and reject combinations where that
    difference is violated (exactly for same-tree-person pairs; within a
    birth-year tolerance for different-tree-person pairs).

    Each hypothesis is scored as the geometric mean of individual cm_scores and
    returned sorted descending.
    """
    # ── Load data ─────────────────────────────────────────────────────────────
    tree_people: dict[int, models.Person] = {p.id: p for p in tree.people}
    cluster_people: dict[int, models.ClusterPerson] = {p.id: p for p in cluster.people}
    cluster_rels: list[models.ClusterRelationship] = cluster.relationships

    # matches grouped by cluster_person_id
    matches_by_cp: dict[int, list[models.Match]] = {}
    for m in tree.matches:
        if m.cluster_person_id in cluster_people:
            matches_by_cp.setdefault(m.cluster_person_id, []).append(m)

    if not matches_by_cp:
        return []

    # ── Build candidate placements per cluster person ─────────────────────────
    # candidates[cp_id] = list of Placement objects
    candidates: dict[int, list[Placement]] = {}

    for cp_id, matches in matches_by_cp.items():
        cp = cluster_people[cp_id]
        cp_candidates: list[Placement] = []

        for match in matches:
            tp = tree_people.get(match.person_id)
            if tp is None:
                continue
            cm = match.centimorgans

            for rel_type, (lo, hi) in CM_RANGES.items():
                if cm < lo or cm > hi:
                    continue
                score = _cm_score(cm, rel_type)
                if score <= 0:
                    continue
                if not _birth_year_ok(tp.birth_year, cp.birth_year, rel_type):
                    continue
                cp_candidates.append(
                    Placement(
                        cluster_person_id=cp_id,
                        cluster_person_name=cp.name,
                        tree_person_id=tp.id,
                        tree_person_name=f"{tp.first_name} {tp.last_name}".strip(),
                        tree_person_birth_year=tp.birth_year,
                        relationship_type=rel_type,
                        centimorgans=cm,
                        cm_score=score,
                    )
                )

        if cp_candidates:
            candidates[cp_id] = cp_candidates

    if not candidates:
        return []

    # ── Enumerate hypothesis combinations ────────────────────────────────────
    cp_ids = list(candidates.keys())
    candidate_lists = [candidates[cid] for cid in cp_ids]

    raw_hypotheses: list[tuple[float, list[PlacementEntry]]] = []

    for combo in product(*candidate_lists):
        # combo is a tuple of Placement, one per cluster person
        if not _combo_consistent(combo, cluster_rels):
            continue

        if not combo:
            continue
        if any(p.cm_score <= 0 for p in combo):
            continue
        score = math.exp(
            sum(math.log(p.cm_score) for p in combo) / len(combo)
        )

        placements = [
            PlacementEntry(
                cluster_person_id=p.cluster_person_id,
                cluster_person_name=p.cluster_person_name,
                tree_person_id=p.tree_person_id,
                tree_person_name=p.tree_person_name,
                relationship=p.relationship_type,
                cm_observed=p.centimorgans,
                cm_min=CM_RANGES[p.relationship_type][0],
                cm_max=CM_RANGES[p.relationship_type][1],
                score=round(p.cm_score, 6),
            )
            for p in combo
        ]
        raw_hypotheses.append((score, placements))

    raw_hypotheses.sort(key=lambda x: x[0], reverse=True)
    raw_hypotheses = raw_hypotheses[:100]

    total_score = sum(s for s, _ in raw_hypotheses)

    return [
        HypothesisOut(
            rank=i + 1,
            score=round(score, 6),
            likelihood_score=round(score, 6),
            likelihood_percent=round((score / total_score) * 100, 4) if total_score > 0 else 0.0,
            placements=placements,
        )
        for i, (score, placements) in enumerate(raw_hypotheses)
    ]


def _combo_consistent(
    combo: tuple[Placement, ...],
    cluster_rels: list[models.ClusterRelationship],
) -> bool:
    """
    Consistency check for a combination of placements against the declared
    inter-cluster relationships.

    For every cluster relationship between two placed cluster persons, we
    derive the expected generational difference between their respective tree-
    person matches and reject the combination when that expectation is violated:

    - Same tree person: the generational distance of that person from each
      cluster person must differ by exactly the inter-cluster generation gap.
    - Different tree persons: when both birth years are known we verify that
      the birth-year difference is consistent with the expected generational
      gap (within ±1.5 generation tolerance).
    """
    placement_by_cp: dict[int, Placement] = {p.cluster_person_id: p for p in combo}

    for rel in cluster_rels:
        p1 = placement_by_cp.get(rel.person1_id)
        p2 = placement_by_cp.get(rel.person2_id)
        if p1 is None or p2 is None:
            continue  # one side not placed — skip

        c_delta = CLUSTER_GEN_DELTA.get(rel.rel_type)
        if c_delta is None:
            continue  # unknown cluster relationship type — skip

        d1 = GEN_DIST.get(p1.relationship_type)
        d2 = GEN_DIST.get(p2.relationship_type)
        if d1 is None or d2 is None:
            continue  # ambiguous generational distance — skip

        # Expected generational difference between the two tree persons:
        # tp1 should be (c_delta + d1 - d2) generations older than tp2.
        # Derivation: G_tp1 = G_cp1 + d1; G_tp2 = G_cp2 + d2;
        #             G_cp1 - G_cp2 = c_delta  →  G_tp1 - G_tp2 = c_delta + d1 - d2
        expected_tp_gen_diff = c_delta + d1 - d2

        if p1.tree_person_id == p2.tree_person_id:
            # Same tree person: the generational gap between the two cluster
            # persons as seen from the same tree node must be zero.
            if expected_tp_gen_diff != 0:
                return False
        else:
            # Different tree persons: use birth years when available.
            by1 = p1.tree_person_birth_year
            by2 = p2.tree_person_birth_year
            if by1 is not None and by2 is not None:
                # tp1 older by expected_tp_gen_diff gens means tp1 born earlier,
                # i.e., by2 - by1 ≈ expected_tp_gen_diff * AVG_GEN_YEARS
                actual_gen_diff = (by2 - by1) / AVG_GEN_YEARS
                if abs(actual_gen_diff - expected_tp_gen_diff) > GEN_BIRTH_TOLERANCE:
                    return False

    return True
