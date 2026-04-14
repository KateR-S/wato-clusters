from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..auth import get_current_user
from ..schemas import MatchCreate, MatchOut

router = APIRouter(prefix="/trees", tags=["matches"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


def _get_tree_or_404(tree_id: int, user: models.User, db: Session) -> models.Tree:
    tree = db.get(models.Tree, tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")
    if tree.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your tree")
    return tree


@router.get("/{tree_id}/matches", response_model=list[MatchOut])
async def list_matches(
    tree_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
):
    _get_tree_or_404(tree_id, current_user, db)
    return db.query(models.Match).filter(models.Match.tree_id == tree_id).all()


@router.post(
    "/{tree_id}/matches", response_model=MatchOut, status_code=status.HTTP_201_CREATED
)
async def add_match(
    tree_id: int,
    body: MatchCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    tree = _get_tree_or_404(tree_id, current_user, db)

    # Validate person belongs to this tree
    person = db.get(models.Person, body.person_id)
    if not person or person.tree_id != tree.id:
        raise HTTPException(status_code=404, detail="Person not found in tree")

    # Validate cluster person exists (any cluster belonging to same user)
    cp = db.get(models.ClusterPerson, body.cluster_person_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Cluster person not found")
    cluster = db.get(models.Cluster, cp.cluster_id)
    if not cluster or cluster.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your cluster person")

    match = models.Match(tree_id=tree.id, **body.model_dump())
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.delete(
    "/{tree_id}/matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_match(
    tree_id: int,
    match_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    _get_tree_or_404(tree_id, current_user, db)
    match = db.get(models.Match, match_id)
    if not match or match.tree_id != tree_id:
        raise HTTPException(status_code=404, detail="Match not found")
    db.delete(match)
    db.commit()
