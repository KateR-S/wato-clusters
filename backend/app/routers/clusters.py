from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..auth import get_current_user
from ..schemas import (
    ClusterCreate, ClusterOut, ClusterDetail,
    ClusterPersonCreate, ClusterPersonUpdate, ClusterPersonOut,
    ClusterRelationshipCreate, ClusterRelationshipOut,
)

router = APIRouter(prefix="/clusters", tags=["clusters"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


def _get_cluster_or_404(cluster_id: int, user: models.User, db: Session) -> models.Cluster:
    cluster = db.get(models.Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if cluster.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your cluster")
    return cluster


def _get_cp_or_404(
    person_id: int, cluster: models.Cluster, db: Session
) -> models.ClusterPerson:
    cp = db.get(models.ClusterPerson, person_id)
    if not cp or cp.cluster_id != cluster.id:
        raise HTTPException(status_code=404, detail="Cluster person not found")
    return cp


# ── Cluster CRUD ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[ClusterOut])
async def list_clusters(current_user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(models.Cluster).filter(models.Cluster.user_id == current_user.id).all()


@router.post("", response_model=ClusterOut, status_code=status.HTTP_201_CREATED)
async def create_cluster(
    body: ClusterCreate, current_user: CurrentUser, db: Session = Depends(get_db)
):
    cluster = models.Cluster(user_id=current_user.id, name=body.name)
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


@router.get("/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(
    cluster_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
):
    return _get_cluster_or_404(cluster_id, current_user, db)


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
):
    cluster = _get_cluster_or_404(cluster_id, current_user, db)
    db.delete(cluster)
    db.commit()


# ── Cluster People CRUD ───────────────────────────────────────────────────────

@router.post(
    "/{cluster_id}/people",
    response_model=ClusterPersonOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_cluster_person(
    cluster_id: int,
    body: ClusterPersonCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    cluster = _get_cluster_or_404(cluster_id, current_user, db)
    cp = models.ClusterPerson(cluster_id=cluster.id, **body.model_dump())
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


@router.put(
    "/{cluster_id}/people/{person_id}", response_model=ClusterPersonOut
)
async def update_cluster_person(
    cluster_id: int,
    person_id: int,
    body: ClusterPersonUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    cluster = _get_cluster_or_404(cluster_id, current_user, db)
    cp = _get_cp_or_404(person_id, cluster, db)
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(cp, key, val)
    db.commit()
    db.refresh(cp)
    return cp


@router.delete(
    "/{cluster_id}/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_cluster_person(
    cluster_id: int,
    person_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    cluster = _get_cluster_or_404(cluster_id, current_user, db)
    cp = _get_cp_or_404(person_id, cluster, db)
    db.delete(cp)
    db.commit()


# ── Cluster Relationships CRUD ────────────────────────────────────────────────

@router.post(
    "/{cluster_id}/relationships",
    response_model=ClusterRelationshipOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_cluster_relationship(
    cluster_id: int,
    body: ClusterRelationshipCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    cluster = _get_cluster_or_404(cluster_id, current_user, db)
    _get_cp_or_404(body.person1_id, cluster, db)
    _get_cp_or_404(body.person2_id, cluster, db)
    rel = models.ClusterRelationship(cluster_id=cluster.id, **body.model_dump())
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


@router.delete(
    "/{cluster_id}/relationships/{rel_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_cluster_relationship(
    cluster_id: int,
    rel_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    cluster = _get_cluster_or_404(cluster_id, current_user, db)
    rel = db.get(models.ClusterRelationship, rel_id)
    if not rel or rel.cluster_id != cluster.id:
        raise HTTPException(status_code=404, detail="Relationship not found")
    db.delete(rel)
    db.commit()
