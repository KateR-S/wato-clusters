from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..auth import get_current_user
from ..schemas import HypothesisRequest, HypothesisOut
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
