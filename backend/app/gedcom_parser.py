"""
GEDCOM file parser.

Tries to use ged4py when available; falls back to a minimal hand-rolled parser
so the application works even if ged4py is not installed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import StringIO
from typing import Optional


@dataclass
class GedcomIndividual:
    gedcom_id: str
    first_name: str = ""
    last_name: str = ""
    sex: str = "U"
    birth_year: Optional[int] = None


@dataclass
class GedcomFamily:
    husband_id: Optional[str] = None
    wife_id: Optional[str] = None
    child_ids: list[str] = field(default_factory=list)


@dataclass
class GedcomData:
    individuals: list[GedcomIndividual] = field(default_factory=list)
    families: list[GedcomFamily] = field(default_factory=list)


# ── Minimal hand-rolled parser ────────────────────────────────────────────────

_YEAR_RE = re.compile(r"\b(\d{4})\b")


def _extract_year(value: str) -> Optional[int]:
    m = _YEAR_RE.search(value)
    return int(m.group(1)) if m else None


def _parse_name(raw: str) -> tuple[str, str]:
    """Parse a GEDCOM NAME value like 'John /Smith/' into (first, last)."""
    raw = raw.strip()
    slash_match = re.match(r"^(.*?)\s*/([^/]*)/", raw)
    if slash_match:
        first = slash_match.group(1).strip()
        last = slash_match.group(2).strip()
    else:
        parts = raw.split()
        first = parts[0] if parts else ""
        last = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first, last


def parse_gedcom(content: str) -> GedcomData:
    """
    Parse a GEDCOM string and return extracted individuals and families.
    Handles both UTF-8 and Latin-1 encoded content passed as a decoded string.
    """
    try:
        return _parse_with_ged4py(content)
    except Exception:
        return _parse_minimal(content)


def _parse_with_ged4py(content: str) -> GedcomData:
    import ged4py
    from ged4py import GedcomReader

    data = GedcomData()
    reader = GedcomReader(StringIO(content))

    for record in reader.records0():
        if record.tag == "INDI":
            indi = GedcomIndividual(gedcom_id=record.xref_id or "")
            name_rec = record.sub_tag("NAME")
            if name_rec and name_rec.value:
                indi.first_name, indi.last_name = _parse_name(str(name_rec.value))
            sex_rec = record.sub_tag("SEX")
            if sex_rec and sex_rec.value:
                sv = str(sex_rec.value).strip().upper()
                indi.sex = sv if sv in ("M", "F") else "U"
            birt = record.sub_tag("BIRT")
            if birt:
                date_rec = birt.sub_tag("DATE")
                if date_rec and date_rec.value:
                    indi.birth_year = _extract_year(str(date_rec.value))
            data.individuals.append(indi)

        elif record.tag == "FAM":
            fam = GedcomFamily()
            husb = record.sub_tag("HUSB")
            if husb and husb.value:
                fam.husband_id = str(husb.value).strip()
            wife = record.sub_tag("WIFE")
            if wife and wife.value:
                fam.wife_id = str(wife.value).strip()
            for chil in record.sub_tags("CHIL"):
                if chil.value:
                    fam.child_ids.append(str(chil.value).strip())
            data.families.append(fam)

    return data


def _parse_minimal(content: str) -> GedcomData:
    """Line-by-line GEDCOM parser that handles the most common tags."""
    data = GedcomData()
    individuals: dict[str, GedcomIndividual] = {}
    families: dict[str, GedcomFamily] = {}

    current_indi: Optional[GedcomIndividual] = None
    current_fam: Optional[GedcomFamily] = None
    in_birt = False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split(None, 2)
        if not parts:
            continue

        level_str = parts[0]
        try:
            level = int(level_str)
        except ValueError:
            continue

        tag = parts[1] if len(parts) > 1 else ""
        value = parts[2] if len(parts) > 2 else ""

        if level == 0:
            current_indi = None
            current_fam = None
            in_birt = False
            # 0 @I1@ INDI  or  0 @F1@ FAM
            xref_id = tag  # second token is the xref_id when level==0 and there's an @
            rec_type = value.split()[0] if value else ""
            if rec_type == "INDI":
                current_indi = GedcomIndividual(gedcom_id=xref_id)
                individuals[xref_id] = current_indi
            elif rec_type == "FAM":
                current_fam = GedcomFamily()
                families[xref_id] = current_fam

        elif level == 1:
            in_birt = False
            if current_indi is not None:
                if tag == "NAME":
                    current_indi.first_name, current_indi.last_name = _parse_name(value)
                elif tag == "SEX":
                    sv = value.strip().upper()
                    current_indi.sex = sv if sv in ("M", "F") else "U"
                elif tag == "BIRT":
                    in_birt = True
            elif current_fam is not None:
                ref = value.strip()
                if tag == "HUSB":
                    current_fam.husband_id = ref
                elif tag == "WIFE":
                    current_fam.wife_id = ref
                elif tag == "CHIL":
                    current_fam.child_ids.append(ref)

        elif level == 2:
            if in_birt and current_indi is not None and tag == "DATE":
                current_indi.birth_year = _extract_year(value)

    data.individuals = list(individuals.values())
    data.families = list(families.values())
    return data
