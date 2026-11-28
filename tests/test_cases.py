import pandas as pd

from src.web.cases import CASES, Facts, _fmt_pct


def test_facts_lookup_by_filing_date():
    tl = pd.DataFrame({"d": ["2022-04-21", "2022-06-29"], "p": [0.986, 0.989]})
    h = pd.DataFrame({"available_date": ["2022-04-21"], "z_score": [4.32], "restatement_pctile": [0.43]})
    f = Facts(tl, h)
    assert f.pct("2022-04-21") == "98%" and f.z("2022-04-21") == "4.32" and f.rpct("2022-04-21") == "43%"
    assert f.pct("2020-01-01") == "n/a"


def test_case_list():
    assert {c["slug"] for c in CASES} == {"sears", "bed-bath-beyond", "general-electric", "kraft-heinz", "svb"}
    assert _fmt_pct(1.0) == "99%"
