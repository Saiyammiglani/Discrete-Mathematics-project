"""Input service tests: validation rules and error messages."""
from services.input import SAMPLES, build_graph, load_sample, parse_csv


def errs(text):
    r = parse_csv(text)
    assert not r.ok
    return dict(r.errors)


def test_samples_load():
    for name in SAMPLES:
        r = load_sample(name)
        assert r.ok and len(r.graph.components()) == 1
    assert load_sample("Office network (8 devices)").graph.total_weight() == 59


def test_valid_csv_and_bom_and_blank_lines():
    r = parse_csv("﻿source,target,weight\nA,B,2\n\nB,C,3.5\n".encode())
    assert r.ok and r.graph.total_weight() == 5.5


def test_header_checked():
    assert 1 in errs("a,b,c\nA,B,1\n")
    assert 0 in errs("")


def test_bad_rows_all_reported_with_row_numbers():
    e = errs("source,target,weight\nA,B,2\n,C,1\nD,D,3\nE,F,0\nG,H,-4\nI,J,abc\nK,L,nan\nM,N\n")
    assert e[3] == "source is empty"
    assert e[4] == "self-loop D–D"
    assert e[5] == "weight must be > 0" and e[6] == "weight must be > 0"
    assert "not a number" in e[7]
    assert e[8] == "weight must be > 0"          # nan
    assert e[9].startswith("expected 3 columns")


def test_name_length_limit():
    assert 2 in errs(f"source,target,weight\n{'x' * 31},B,1\n")


def test_duplicate_keeps_cheapest_and_says_so():
    r = parse_csv("source,target,weight\nSA,SB,5\nSB,SA,2\n")
    assert r.ok and r.graph.weight("SA", "SB") == 2
    assert r.infos == ["SA–SB listed twice, kept 2"]


def test_size_cap_and_encoding():
    assert 0 in dict(parse_csv(b"x" * 1_000_001).errors)
    assert 0 in dict(parse_csv(b"\xff\xfe\x00").errors)


def test_no_links():
    assert not parse_csv("source,target,weight\n").ok
    assert not build_graph([]).ok
