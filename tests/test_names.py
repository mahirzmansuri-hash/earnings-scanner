from src.pipeline.names import nice_case, pick


def test_entity_name_keeps_punctuation():
    assert pick("AMERICAS CARMART INC", "AMERICA’S CAR-MART, INC.") == "America's Car-Mart, Inc."


def test_acronyms_and_small_words():
    assert nice_case("JPMORGAN CHASE & CO") == "JPMorgan Chase & Co"
    assert nice_case("BANK OF AMERICA CORP") == "Bank of America Corp"
    assert nice_case("3M CO") == "3M Co"
    assert nice_case("CVS HEALTH CORP") == "CVS Health Corp"


def test_state_tag_and_mixed_case():
    assert pick("CLOROX CO /DE/", None) == "Clorox Co"
    assert pick("Apple Inc.", "Apple Inc.") == "Apple Inc."
    assert pick("SEARS HOLDINGS CORP", "SOMETHING ELSE INC") == "Sears Holdings Corp"   # different name: keep SEC's
