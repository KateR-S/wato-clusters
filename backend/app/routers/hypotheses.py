from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..auth import get_current_user
from ..schemas import HypothesisRequest, HypothesisOut, EvaluateRequest
from ..hypothesis_engine import generate_hypotheses

router = APIRouter(prefix="/trees", tags=["hypotheses"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


@router.post("/{tree_id}/hypotheses", response_model=list[HypothesisOut])
async def get_hypotheses(
    tree_id: int,
    body: HypothesisRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    tree = db.get(models.Tree, tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")
    if tree.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your tree")

    cluster = db.get(models.Cluster, body.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if cluster.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your cluster")

    return generate_hypotheses(db, tree, cluster)


@router.post("/{tree_id}/evaluate", response_model=list[HypothesisOut])
async def evaluate_placement(
    tree_id: int,
    body: EvaluateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Evaluate how well a set of posited (cluster_person, tree_person,
    relationship) anchors fits the observed centimorgan data.

    The specified anchors are treated as fixed constraints.  All other
    (cluster_person, tree_person) match pairs in the dataset are assigned
    the best-fitting relationship type consistent with the anchors.

    Returns the same ranked HypothesisOut list as the standard hypotheses
    endpoint, but filtered to hypotheses that satisfy every anchor.  Each
    entry's score reflects how well all cM values — including out-of-range
    anchors — fit the posited and derived relationships.
    """
    tree = db.get(models.Tree, tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")
    if tree.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your tree")

    cluster = db.get(models.Cluster, body.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if cluster.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your cluster")

    locked_pairs = {
        (a.cluster_person_id, a.tree_person_id): a.relationship
        for a in body.anchors
    }
    return generate_hypotheses(db, tree, cluster, locked_pairs=locked_pairs)
