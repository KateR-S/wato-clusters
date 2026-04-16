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
# Kept for birth-year fallback (used when tree generation data is unavailable).
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

# All *possible* generational distances per relationship type.
# "Once removed" relationships (1r) can run in either direction (±1); "twice
# removed" (2r) can be ±2.  This replaces the single-valued GEN_DIST for the
# exact consistency checks when tree generation numbers are available.
GEN_DIST_POSSIBLE: dict[str, set[int]] = {
    "parent":            {1},
    "child":             {-1},
    "full_sibling":      {0},
    "half_sibling":      {0},
    "grandparent":       {2},
    "grandchild":        {-2},
    "aunt_uncle":        {1},
    "niece_nephew":      {-1},
    "half_aunt_uncle":   {1},
    "half_niece_nephew": {-1},
    "great_grandparent": {3},
    "great_grandchild":  {-3},
    "1st_cousin":        {0},
    "half_1st_cousin":   {0},
    "1st_cousin_1r":     {1, -1},   # once removed: +1 or -1
    "2nd_cousin":        {0},
    "1st_cousin_2r":     {2, -2},   # twice removed: +2 or -2
    "2nd_cousin_1r":     {1, -1},   # once removed: +1 or -1
    "3rd_cousin":        {0},
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


def _build_tree_generations(
    tree_rels: list[models.Relationship],
    person_ids: set[int],
) -> dict[int, int]:
    """
    Assign an integer generation number to each tree person by BFS over the
    direct tree relationships.  Higher number = older generation.

    Returns a dict mapping person_id → generation number.  Persons that are
    not connected to any other person (isolated nodes) are assigned generation
    0.  Persons with no path to the BFS start are omitted; in practice all
    persons in a well-formed tree should be reachable.
    """
    # adjacency: (neighbor_id, gen_delta) where gen_delta = gen[neighbor] - gen[self]
    adj: dict[int, list[tuple[int, int]]] = {pid: [] for pid in person_ids}
    for rel in tree_rels:
        p1, p2 = rel.person1_id, rel.person2_id
        # rel_type is stored as a string in SQLAlchemy's Enum column but may be
        # returned as either the raw string or the enum object depending on the
        # driver; normalise to string value to be safe.
        rtype = rel.rel_type.value if hasattr(rel.rel_type, "value") else rel.rel_type
        if rtype in ("parent", "half_parent"):
            # p1 is older (parent) → gen[p2] = gen[p1] - 1
            adj[p1].append((p2, -1))
            adj[p2].append((p1, +1))
        elif rtype in ("child", "half_child"):
            # p1 is younger (child) → gen[p2] = gen[p1] + 1
            adj[p1].append((p2, +1))
            adj[p2].append((p1, -1))
        elif rtype in ("full_sibling", "half_sibling", "spouse"):
            adj[p1].append((p2, 0))
            adj[p2].append((p1, 0))

    if not person_ids:
        return {}

    gen: dict[int, int] = {}
    # BFS from each unvisited person to handle disconnected components
    for start in person_ids:
        if start in gen:
            continue
        gen[start] = 0
        queue: list[int] = [start]
        while queue:
            next_queue: list[int] = []
            for curr in queue:
                for neighbor, delta in adj.get(curr, []):
                    if neighbor not in gen:
                        gen[neighbor] = gen[curr] + delta
                        next_queue.append(neighbor)
            queue = next_queue

    return gen


def _pair_gen_dist_ok(required_d_diff: int, rel1: str, rel2: str) -> bool:
    """
    Return True if there exist d1 ∈ GEN_DIST_POSSIBLE[rel1] and
    d2 ∈ GEN_DIST_POSSIBLE[rel2] such that d1 - d2 == required_d_diff.

    Returns True (unchecked) if either relationship type is not in the table.
    """
    p1 = GEN_DIST_POSSIBLE.get(rel1)
    p2 = GEN_DIST_POSSIBLE.get(rel2)
    if not p1 or not p2:
        return True
    return any((d1 - required_d_diff) in p2 for d1 in p1)


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
    Every recorded (cluster_person, tree_person) cM match defines a pair.
    For each such pair we enumerate every relationship type whose cM range
    contains the observed value and whose birth years are compatible.

    A *hypothesis* is one consistent assignment of a relationship type to
    every match pair.  Every hypothesis therefore contains exactly one
    PlacementEntry per (cluster_person, tree_person) match pair — giving the
    full cross-product view requested by the user.

    Consistency means that for every cluster relationship (e.g. A is the
    half-sibling of B), all placements involving A and B must respect the
    implied generational ordering:
      - When A and B are both matched to the same tree person, the
        generational distances must satisfy the cluster relationship exactly.
      - When they are matched to different tree persons, birth years are used
        as a proxy (within ±1.5 generation tolerance).

    Each hypothesis is scored as the geometric mean of individual cm_scores
    and returned sorted descending.
    """
    # ── Load data ─────────────────────────────────────────────────────────────
    tree_people: dict[int, models.Person] = {p.id: p for p in tree.people}
    cluster_people: dict[int, models.ClusterPerson] = {p.id: p for p in cluster.people}
    cluster_rels: list[models.ClusterRelationship] = cluster.relationships

    # Build generation numbers for all tree persons from the tree's relationships
    tree_gen: dict[int, int] = _build_tree_generations(
        tree.relationships, set(tree_people.keys())
    )

    # matches grouped by cluster_person_id
    matches_by_cp: dict[int, list[models.Match]] = {}
    for m in tree.matches:
        if m.cluster_person_id in cluster_people:
            matches_by_cp.setdefault(m.cluster_person_id, []).append(m)

    if not matches_by_cp:
        return []

    # ── Build candidate relationship types per (cluster_person, tree_person) pair ─
    # pair_candidates[(cp_id, tp_id)] = list of Placement, one per valid rel type.
    # The enumeration picks exactly ONE element from each list, so every hypothesis
    # contains one PlacementEntry per match pair.
    pair_candidates: dict[tuple[int, int], list[Placement]] = {}

    for cp_id, matches in matches_by_cp.items():
        cp = cluster_people[cp_id]

        for match in matches:
            tp = tree_people.get(match.person_id)
            if tp is None:
                continue
            cm = match.centimorgans
            pair = (cp_id, tp.id)
            pair_cands: list[Placement] = []

            for rel_type, (lo, hi) in CM_RANGES.items():
                if cm < lo or cm > hi:
                    continue
                score = _cm_score(cm, rel_type)
                if score <= 0:
                    continue
                if not _birth_year_ok(tp.birth_year, cp.birth_year, rel_type):
                    continue
                pair_cands.append(
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

            if pair_cands:
                pair_candidates[pair] = pair_cands

    if not pair_candidates:
        return []

    # ── Enumerate hypothesis combinations ────────────────────────────────────
    # product picks one rel-type assignment per (cp, tp) pair.
    candidate_lists = list(pair_candidates.values())

    raw_hypotheses: list[tuple[float, list[PlacementEntry]]] = []

    for combo in product(*candidate_lists):
        if not combo:
            continue
        if any(p.cm_score <= 0 for p in combo):
            continue
        if not _combo_consistent(combo, cluster_rels, tree_gen):
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
    tree_gen: Optional[dict[int, int]] = None,
) -> bool:
    """
    Consistency check for a combination of placements.

    Unified constraint
    ------------------
    For any two placements p1 (cluster person cp1 → tree person T1, rel1) and
    p2 (cluster person cp2 → tree person T2, rel2) where cp1 and cp2 have a
    known generational gap c_delta = G(cp1) - G(cp2):

        d1 - d2  =  (gen[T1] - gen[T2])  -  c_delta

    where d1 ∈ GEN_DIST_POSSIBLE[rel1] and d2 ∈ GEN_DIST_POSSIBLE[rel2].

    This single formula covers:
      • Same cluster person (c_delta = 0), placements to different tree
        persons (Check A): enforces that the cluster person is at a
        self-consistent generational level across all matched tree persons.
      • Different cluster persons with a known relationship, any pair of
        their tree placements (Check B): enforces that the inter-cluster
        generational gap is reflected in the tree placements.

    When exact tree generation numbers are unavailable (tree_gen is empty or a
    tree person is not in it), the function falls back to birth-year tolerance
    for cross-tree-person pairs and to GEN_DIST_POSSIBLE for same-tree-person
    pairs.
    """
    if tree_gen is None:
        tree_gen = {}

    # Group placements by cluster person (multiple entries per cp in new model)
    placements_by_cp: dict[int, list[Placement]] = {}
    for p in combo:
        placements_by_cp.setdefault(p.cluster_person_id, []).append(p)

    def _check_pair(p1: Placement, p2: Placement, c_delta: int) -> bool:
        """
        Return False if p1 and p2 violate the unified generational constraint
        given the cluster-level generation gap c_delta = G(cp1) - G(cp2).
        """
        t1_gen = tree_gen.get(p1.tree_person_id)
        t2_gen = tree_gen.get(p2.tree_person_id)

        if t1_gen is not None and t2_gen is not None:
            # Exact check using tree generation numbers.
            required = (t1_gen - t2_gen) - c_delta
            return _pair_gen_dist_ok(required, p1.relationship_type, p2.relationship_type)

        # ── Fallback when exact tree gen data is unavailable ──────────────
        if p1.tree_person_id == p2.tree_person_id:
            # Same tree person → tree_gd = 0 exactly.
            required = -c_delta
            return _pair_gen_dist_ok(required, p1.relationship_type, p2.relationship_type)
        else:
            # Different tree persons: approximate via birth years.
            by1 = p1.tree_person_birth_year
            by2 = p2.tree_person_birth_year
            if by1 is not None and by2 is not None:
                # higher gen = older = earlier birth year
                # gen[T1] - gen[T2] ≈ (by2 - by1) / AVG_GEN_YEARS
                actual_tree_gd = (by2 - by1) / AVG_GEN_YEARS
                d1 = GEN_DIST.get(p1.relationship_type)
                d2 = GEN_DIST.get(p2.relationship_type)
                if d1 is not None and d2 is not None:
                    # expected tree_gd = (d1 - d2) + c_delta
                    if abs(actual_tree_gd - ((d1 - d2) + c_delta)) > GEN_BIRTH_TOLERANCE:
                        return False
        return True

    # ── Check A: same cluster person, all pairs of their tree-person placements ──
    for plist in placements_by_cp.values():
        for i in range(len(plist)):
            for j in range(i + 1, len(plist)):
                if not _check_pair(plist[i], plist[j], c_delta=0):
                    return False

    # ── Check B: pairs across different cluster persons with a known relationship ─
    for rel in cluster_rels:
        plist1 = placements_by_cp.get(rel.person1_id, [])
        plist2 = placements_by_cp.get(rel.person2_id, [])
        c_delta = CLUSTER_GEN_DELTA.get(rel.rel_type)
        if c_delta is None:
            continue
        for p1 in plist1:
            for p2 in plist2:
                if not _check_pair(p1, p2, c_delta=c_delta):
                    return False

    return True
