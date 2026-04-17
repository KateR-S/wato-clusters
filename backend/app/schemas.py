from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Person ────────────────────────────────────────────────────────────────────

class PersonCreate(BaseModel):
    first_name: str
    last_name: str = ""
    birth_year: Optional[int] = None
    sex: str = "U"
    notes: Optional[str] = None

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        if v not in ("M", "F", "U"):
            raise ValueError("sex must be M, F, or U")
        return v


class PersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_year: Optional[int] = None
    sex: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("M", "F", "U"):
            raise ValueError("sex must be M, F, or U")
        return v


class PersonOut(BaseModel):
    id: int
    tree_id: int
    gedcom_id: Optional[str] = None
    first_name: str
    last_name: str
    birth_year: Optional[int] = None
    sex: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Relationship ──────────────────────────────────────────────────────────────

VALID_REL_TYPES = {
    "parent", "child", "spouse", "half_sibling",
    "half_parent", "half_child", "full_sibling",
}


class RelationshipCreate(BaseModel):
    person1_id: int
    person2_id: int
    rel_type: str

    @field_validator("rel_type")
    @classmethod
    def validate_rel_type(cls, v: str) -> str:
        if v not in VALID_REL_TYPES:
            raise ValueError(f"rel_type must be one of {VALID_REL_TYPES}")
        return v


class RelationshipOut(BaseModel):
    id: int
    tree_id: int
    person1_id: int
    person2_id: int
    rel_type: str

    model_config = {"from_attributes": True}


# ── Tree ──────────────────────────────────────────────────────────────────────

class TreeCreate(BaseModel):
    name: str


class TreeUpdate(BaseModel):
    name: str


class TreeOut(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TreeDetail(TreeOut):
    people: list[PersonOut] = []
    relationships: list[RelationshipOut] = []


# ── Cluster Person ────────────────────────────────────────────────────────────

class ClusterPersonCreate(BaseModel):
    name: str
    birth_year: Optional[int] = None
    notes: Optional[str] = None


class ClusterPersonUpdate(BaseModel):
    name: Optional[str] = None
    birth_year: Optional[int] = None
    notes: Optional[str] = None


class ClusterPersonOut(BaseModel):
    id: int
    cluster_id: int
    name: str
    birth_year: Optional[int] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Cluster Relationship ──────────────────────────────────────────────────────

class ClusterRelationshipCreate(BaseModel):
    person1_id: int
    person2_id: int
    rel_type: str

    @field_validator("rel_type")
    @classmethod
    def validate_rel_type(cls, v: str) -> str:
        if v not in VALID_REL_TYPES:
            raise ValueError(f"rel_type must be one of {VALID_REL_TYPES}")
        return v


class ClusterRelationshipOut(BaseModel):
    id: int
    cluster_id: int
    person1_id: int
    person2_id: int
    rel_type: str

    model_config = {"from_attributes": True}


# ── Cluster ───────────────────────────────────────────────────────────────────

class ClusterCreate(BaseModel):
    name: str


class ClusterOut(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClusterDetail(ClusterOut):
    people: list[ClusterPersonOut] = []
    relationships: list[ClusterRelationshipOut] = []


# ── Match ─────────────────────────────────────────────────────────────────────

class MatchCreate(BaseModel):
    person_id: int
    cluster_person_id: int
    centimorgans: float


class MatchOut(BaseModel):
    id: int
    tree_id: int
    person_id: int
    cluster_person_id: int
    centimorgans: float

    model_config = {"from_attributes": True}


# ── Hypothesis ────────────────────────────────────────────────────────────────

class HypothesisRequest(BaseModel):
    cluster_id: int


class AnchorEntry(BaseModel):
    """A single posited (cluster_person, tree_person, relationship) anchor."""
    cluster_person_id: int
    tree_person_id: int
    relationship: str


class EvaluateRequest(BaseModel):
    cluster_id: int
    anchors: list[AnchorEntry]


class PlacementEntry(BaseModel):
    cluster_person_id: int
    cluster_person_name: str
    tree_person_id: int
    tree_person_name: str
    relationship: str
    cm_observed: float
    cm_min: float
    cm_max: float
    score: float


class HypothesisOut(BaseModel):
    rank: int
    score: float
    likelihood_score: float
    likelihood_percent: float
    placements: list[PlacementEntry]
