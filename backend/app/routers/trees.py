from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..auth import get_current_user
from ..schemas import (
    TreeCreate, TreeUpdate, TreeOut, TreeDetail,
    PersonCreate, PersonUpdate, PersonOut,
    RelationshipCreate, RelationshipOut,
)
from ..gedcom_parser import parse_gedcom

router = APIRouter(prefix="/trees", tags=["trees"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


def _get_tree_or_404(tree_id: int, user: models.User, db: Session) -> models.Tree:
    tree = db.get(models.Tree, tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")
    if tree.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your tree")
    return tree


def _get_person_or_404(person_id: int, tree: models.Tree, db: Session) -> models.Person:
    person = db.get(models.Person, person_id)
    if not person or person.tree_id != tree.id:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


# ── Tree CRUD ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[TreeOut])
async def list_trees(current_user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(models.Tree).filter(models.Tree.user_id == current_user.id).all()


@router.post("", response_model=TreeOut, status_code=status.HTTP_201_CREATED)
async def create_tree(body: TreeCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    tree = models.Tree(user_id=current_user.id, name=body.name)
    db.add(tree)
    db.commit()
    db.refresh(tree)
    return tree


@router.get("/{tree_id}", response_model=TreeDetail)
async def get_tree(tree_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    return _get_tree_or_404(tree_id, current_user, db)


@router.put("/{tree_id}", response_model=TreeOut)
async def update_tree(
    tree_id: int, body: TreeUpdate, current_user: CurrentUser, db: Session = Depends(get_db)
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    tree.name = body.name
    db.commit()
    db.refresh(tree)
    return tree


@router.delete("/{tree_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tree(tree_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    tree = _get_tree_or_404(tree_id, current_user, db)
    db.delete(tree)
    db.commit()


# ── People CRUD ───────────────────────────────────────────────────────────────

@router.post("/{tree_id}/people", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
async def add_person(
    tree_id: int, body: PersonCreate, current_user: CurrentUser, db: Session = Depends(get_db)
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    person = models.Person(tree_id=tree.id, **body.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.put("/{tree_id}/people/{person_id}", response_model=PersonOut)
async def update_person(
    tree_id: int,
    person_id: int,
    body: PersonUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    person = _get_person_or_404(person_id, tree, db)
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(person, key, val)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/{tree_id}/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    tree_id: int, person_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    person = _get_person_or_404(person_id, tree, db)
    db.delete(person)
    db.commit()


# ── Relationships CRUD ────────────────────────────────────────────────────────

@router.post(
    "/{tree_id}/relationships",
    response_model=RelationshipOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_relationship(
    tree_id: int,
    body: RelationshipCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    _get_person_or_404(body.person1_id, tree, db)
    _get_person_or_404(body.person2_id, tree, db)
    rel = models.Relationship(tree_id=tree.id, **body.model_dump())
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


@router.delete(
    "/{tree_id}/relationships/{rel_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_relationship(
    tree_id: int, rel_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    rel = db.get(models.Relationship, rel_id)
    if not rel or rel.tree_id != tree.id:
        raise HTTPException(status_code=404, detail="Relationship not found")
    db.delete(rel)
    db.commit()


# ── GEDCOM upload ─────────────────────────────────────────────────────────────

@router.post("/{tree_id}/gedcom", response_model=TreeDetail)
async def upload_gedcom(
    tree_id: int,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    tree = _get_tree_or_404(tree_id, current_user, db)
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    gedcom_data = parse_gedcom(content)

    # Map gedcom_id → db Person.id
    id_map: dict[str, int] = {}

    for indi in gedcom_data.individuals:
        person = models.Person(
            tree_id=tree.id,
            gedcom_id=indi.gedcom_id,
            first_name=indi.first_name,
            last_name=indi.last_name,
            sex=indi.sex,
            birth_year=indi.birth_year,
        )
        db.add(person)
        db.flush()
        id_map[indi.gedcom_id] = person.id

    for fam in gedcom_data.families:
        parent_ids = []
        if fam.husband_id and fam.husband_id in id_map:
            parent_ids.append(id_map[fam.husband_id])
        if fam.wife_id and fam.wife_id in id_map:
            parent_ids.append(id_map[fam.wife_id])

        # Spouse relationship
        if len(parent_ids) == 2:
            db.add(models.Relationship(
                tree_id=tree.id,
                person1_id=parent_ids[0],
                person2_id=parent_ids[1],
                rel_type="spouse",
            ))

        # Parent/child relationships
        for child_gedcom_id in fam.child_ids:
            if child_gedcom_id not in id_map:
                continue
            child_db_id = id_map[child_gedcom_id]
            for parent_db_id in parent_ids:
                db.add(models.Relationship(
                    tree_id=tree.id,
                    person1_id=parent_db_id,
                    person2_id=child_db_id,
                    rel_type="parent",
                ))
                db.add(models.Relationship(
                    tree_id=tree.id,
                    person1_id=child_db_id,
                    person2_id=parent_db_id,
                    rel_type="child",
                ))

    db.commit()
    db.refresh(tree)
    return tree
