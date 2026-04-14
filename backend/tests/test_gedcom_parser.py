import pytest
from app.gedcom_parser import parse_gedcom


SAMPLE_GEDCOM = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
1 BIRT
2 DATE 15 JAN 1950
0 @I2@ INDI
1 NAME Mary /Jones/
1 SEX F
1 BIRT
2 DATE 3 MAY 1952
0 @I3@ INDI
1 NAME Bobby /Smith/
1 SEX M
1 BIRT
2 DATE 20 DEC 1975
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
0 TRLR
"""


def test_parse_individuals():
    data = parse_gedcom(SAMPLE_GEDCOM)
    assert len(data.individuals) == 3
    ids = {i.gedcom_id for i in data.individuals}
    assert "@I1@" in ids
    assert "@I2@" in ids
    assert "@I3@" in ids


def test_parse_names():
    data = parse_gedcom(SAMPLE_GEDCOM)
    by_id = {i.gedcom_id: i for i in data.individuals}
    assert by_id["@I1@"].first_name == "John"
    assert by_id["@I1@"].last_name == "Smith"
    assert by_id["@I2@"].first_name == "Mary"
    assert by_id["@I2@"].last_name == "Jones"


def test_parse_sex():
    data = parse_gedcom(SAMPLE_GEDCOM)
    by_id = {i.gedcom_id: i for i in data.individuals}
    assert by_id["@I1@"].sex == "M"
    assert by_id["@I2@"].sex == "F"


def test_parse_birth_year():
    data = parse_gedcom(SAMPLE_GEDCOM)
    by_id = {i.gedcom_id: i for i in data.individuals}
    assert by_id["@I1@"].birth_year == 1950
    assert by_id["@I2@"].birth_year == 1952
    assert by_id["@I3@"].birth_year == 1975


def test_parse_family():
    data = parse_gedcom(SAMPLE_GEDCOM)
    assert len(data.families) == 1
    fam = data.families[0]
    assert fam.husband_id == "@I1@"
    assert fam.wife_id == "@I2@"
    assert "@I3@" in fam.child_ids


def test_parse_empty():
    data = parse_gedcom("0 HEAD\n0 TRLR\n")
    assert data.individuals == []
    assert data.families == []


def test_parse_no_birth_year():
    gedcom = """0 HEAD
0 @I1@ INDI
1 NAME Test /Person/
1 SEX U
0 TRLR
"""
    data = parse_gedcom(gedcom)
    assert data.individuals[0].birth_year is None


def test_parse_name_no_slashes():
    gedcom = """0 HEAD
0 @I1@ INDI
1 NAME FirstOnly
0 TRLR
"""
    data = parse_gedcom(gedcom)
    assert data.individuals[0].first_name == "FirstOnly"
