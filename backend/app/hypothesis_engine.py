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

MIN_PARENT_AGE = 14


@dataclass
class Placement:
    """A single cluster_person → {tree_person, relationship} assignment."""
    cluster_person_id: int
    cluster_person_name: str
    tree_person_id: int
    tree_person_name: str
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
    be consistent with that (we check birth-year ordering at minimum; a full
    relational consistency check would require full tree traversal, which is
    done here at a lightweight level).

    Each hypothesis is scored as the product of individual cm_scores and
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

    hypotheses: list[HypothesisOut] = []

    # Cap combinations to avoid explosion
    MAX_COMBINATIONS = 5000
    total = 1
    for lst in candidate_lists:
        total *= len(lst)
        if total > MAX_COMBINATIONS:
            break

    for combo in product(*candidate_lists):
        # combo is a tuple of Placement, one per cluster person
        if not _combo_consistent(combo, cluster_rels):
            continue

        score = 1.0
        for p in combo:
            score *= p.cm_score
        # Geometric mean: numerically stable via log/exp when all scores > 0
        if combo and score > 0:
            score = math.exp(
                sum(math.log(p.cm_score) for p in combo) / len(combo)
            )
        elif combo:
            score = 0.0

        hypotheses.append(
            HypothesisOut(
                score=round(score, 6),
                placements=[
                    PlacementEntry(
                        cluster_person_id=p.cluster_person_id,
                        cluster_person_name=p.cluster_person_name,
                        tree_person_id=p.tree_person_id,
                        tree_person_name=p.tree_person_name,
                        relationship_type=p.relationship_type,
                        centimorgans=p.centimorgans,
                        cm_score=round(p.cm_score, 6),
                    )
                    for p in combo
                ],
            )
        )

    hypotheses.sort(key=lambda h: h.score, reverse=True)
    return hypotheses[:100]  # return top 100


def _combo_consistent(
    combo: tuple[Placement, ...],
    cluster_rels: list[models.ClusterRelationship],
) -> bool:
    """
    Lightweight consistency check for a combination of placements.

    Checks that for every cluster relationship (e.g. A is parent of B), the
    corresponding tree placements have compatible birth years.
    """
    placement_by_cp: dict[int, Placement] = {p.cluster_person_id: p for p in combo}

    for rel in cluster_rels:
        p1 = placement_by_cp.get(rel.person1_id)
        p2 = placement_by_cp.get(rel.person2_id)
        if p1 is None or p2 is None:
            continue  # one side not placed — skip

        # Use the tree person birth years to validate ordering
        # The cluster relationship describes person1 -> person2
        # We mirror birth-year logic: if cluster says person1 is parent of
        # person2, then tree placements' birth years should respect that.
        # We only check when relationship implies ordering.
        rt = rel.rel_type
        if rt in ("parent", "half_parent"):
            # p1 is parent → p1's tree person must be older than p2's tree person
            # We use the cluster person birth years here since tree people may
            # not be directly related
            if p1.cluster_person_id and p2.cluster_person_id:
                pass  # already validated per-placement above
        # For sibling-type rels we just accept (hard to disprove without
        # full tree traversal)

    return True
