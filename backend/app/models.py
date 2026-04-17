from datetime import datetime, timezone
from sqlalchemy import (
    Integer, String, Float, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
import enum


class SexEnum(str, enum.Enum):
    M = "M"
    F = "F"
    U = "U"


class RelTypeEnum(str, enum.Enum):
    parent = "parent"
    child = "child"
    spouse = "spouse"
    half_sibling = "half_sibling"
    half_parent = "half_parent"
    half_child = "half_child"
    full_sibling = "full_sibling"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    trees: Mapped[list["Tree"]] = relationship("Tree", back_populates="owner", cascade="all, delete-orphan")
    clusters: Mapped[list["Cluster"]] = relationship("Cluster", back_populates="owner", cascade="all, delete-orphan")


class Tree(Base):
    __tablename__ = "trees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship("User", back_populates="trees")
    people: Mapped[list["Person"]] = relationship("Person", back_populates="tree", cascade="all, delete-orphan")
    relationships: Mapped[list["Relationship"]] = relationship("Relationship", back_populates="tree", cascade="all, delete-orphan")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="tree", cascade="all, delete-orphan")


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tree_id: Mapped[int] = mapped_column(Integer, ForeignKey("trees.id"), nullable=False)
    gedcom_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str] = mapped_column(Enum(SexEnum), default="U", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tree: Mapped["Tree"] = relationship("Tree", back_populates="people")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="person", cascade="all, delete-orphan")


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tree_id: Mapped[int] = mapped_column(Integer, ForeignKey("trees.id"), nullable=False)
    person1_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id"), nullable=False)
    person2_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id"), nullable=False)
    rel_type: Mapped[str] = mapped_column(Enum(RelTypeEnum), nullable=False)

    tree: Mapped["Tree"] = relationship("Tree", back_populates="relationships")
    person1: Mapped["Person"] = relationship("Person", foreign_keys=[person1_id])
    person2: Mapped["Person"] = relationship("Person", foreign_keys=[person2_id])


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship("User", back_populates="clusters")
    people: Mapped[list["ClusterPerson"]] = relationship("ClusterPerson", back_populates="cluster", cascade="all, delete-orphan")
    relationships: Mapped[list["ClusterRelationship"]] = relationship("ClusterRelationship", back_populates="cluster", cascade="all, delete-orphan")


class ClusterPerson(Base):
    __tablename__ = "cluster_people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_id: Mapped[int] = mapped_column(Integer, ForeignKey("clusters.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="people")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="cluster_person", cascade="all, delete-orphan")


class ClusterRelationship(Base):
    __tablename__ = "cluster_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_id: Mapped[int] = mapped_column(Integer, ForeignKey("clusters.id"), nullable=False)
    person1_id: Mapped[int] = mapped_column(Integer, ForeignKey("cluster_people.id"), nullable=False)
    person2_id: Mapped[int] = mapped_column(Integer, ForeignKey("cluster_people.id"), nullable=False)
    rel_type: Mapped[str] = mapped_column(Enum(RelTypeEnum), nullable=False)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="relationships")
    person1: Mapped["ClusterPerson"] = relationship("ClusterPerson", foreign_keys=[person1_id])
    person2: Mapped["ClusterPerson"] = relationship("ClusterPerson", foreign_keys=[person2_id])


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tree_id: Mapped[int] = mapped_column(Integer, ForeignKey("trees.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id"), nullable=False)
    cluster_person_id: Mapped[int] = mapped_column(Integer, ForeignKey("cluster_people.id"), nullable=False)
    centimorgans: Mapped[float] = mapped_column(Float, nullable=False)

    tree: Mapped["Tree"] = relationship("Tree", back_populates="matches")
    person: Mapped["Person"] = relationship("Person", back_populates="matches")
    cluster_person: Mapped["ClusterPerson"] = relationship("ClusterPerson", back_populates="matches")
