""" Test the miflaga flask app end to end with webtest. """

import random

import webtest

import main


def test_get():
    """ GET / serves the Hebrew, right-to-left page. """
    application = webtest.TestApp(main.app)

    response = application.get('/')
    assert response.status_int == 200
    assert 'lang="he"' in response.text
    assert 'dir="rtl"' in response.text
    assert "מפלגה" in response.text
    assert "מוגש על ידי מארק ולצר" in response.text
    assert "mailto:mark.veltzer@gmail.com" in response.text


def test_static_assets():
    """ The page's stylesheet, script and favicon are served. """
    application = webtest.TestApp(main.app)

    for path, content_type in (
        ("/static/style.css", "text/css"),
        ("/static/app.js", "text/javascript"),
        ("/static/favicon.svg", "image/svg+xml"),
    ):
        response = application.get(path)
        assert response.status_int == 200
        assert response.content_type == content_type

    response = application.get('/favicon.ico')
    assert response.status_int == 302
    assert response.location.endswith("/static/favicon.svg")


def test_name_endpoint():
    """ /app/name returns a two word party name built from its parts. """
    application = webtest.TestApp(main.app)

    response = application.get('/app/name')
    assert response.status_int == 200
    party = response.json
    assert party["name"] == f"{party['noun']} {party['adjective']}"
    assert party["kind"] in ("positive-negative", "negative-positive")
    assert 2 <= len(party["letters"]) <= 3


def test_word_bank_shape():
    """ Every noun has a gender and number; every descriptor has all forms. """
    words = main.app.config["words"]
    for key in ("positive_nouns", "negative_nouns"):
        assert words[key]
        for noun in words[key]:
            assert noun["word"]
            assert noun["gender"] in ("m", "f")
            assert noun["number"] in ("s", "p")
            assert set(noun) <= {"word", "gender", "number", "weight"}
            assert isinstance(noun.get("weight", 1), int) and noun.get("weight", 1) >= 1
    for key in ("positive_descriptors", "negative_descriptors"):
        assert words[key]
        for descriptor in words[key]:
            forms = set(descriptor) - {"weight"}
            if "all" in descriptor:
                assert forms == {"all"}
            else:
                assert forms == {"ms", "fs", "mp", "fp"}
            assert all(descriptor.values())
            assert isinstance(descriptor.get("weight", 1), int) and descriptor.get("weight", 1) >= 1


def test_word_bank_has_no_duplicates():
    """ Each word appears once per list. """
    words = main.app.config["words"]
    for key in ("positive_nouns", "negative_nouns"):
        seen = [noun["word"] for noun in words[key]]
        assert len(seen) == len(set(seen)), key
    for key in ("positive_descriptors", "negative_descriptors"):
        seen = [descriptor.get("all", descriptor.get("ms")) for descriptor in words[key]]
        assert len(seen) == len(set(seen)), key


def test_pick_honors_weights():
    """ A heavier entry comes up in proportion to its weight. """
    pool = [{"word": "light"}, {"word": "heavy", "weight": 9}]
    rng = random.Random(7)
    heavy = sum(main.pick(pool, rng)["word"] == "heavy" for _ in range(5000))
    assert 4300 < heavy < 4700


def test_party_words_dominate():
    """ Words from real party names carry weight, so most names echo one. """
    words = main.app.config["words"]
    party_nouns = {n["word"] for n in words["positive_nouns"] if n.get("weight", 1) > 1}
    assert {"ליכוד", "עתיד", "תקווה", "עוצמה", "מחנה"} <= party_nouns
    rng = random.Random(42)
    hits = 0
    total = 2000
    for _ in range(total):
        party = main.make_name(words, rng)
        if party["kind"] == "positive-negative" and party["noun"] in party_nouns:
            hits += 1
    # half the draws are positive nouns; well over half of those are party words
    assert hits > total * 0.25


def test_ballot_letters_are_hebrew():
    """ The ballot code is Hebrew even for a descriptor like "2026". """
    rng = random.Random(3)
    letters = main.ballot_letters("שקר", "2026", rng)
    assert all(letter in main.HEBREW_LETTERS for letter in letters)
    assert letters[0] == "ש"


def test_describe_agrees():
    """ The descriptor form follows the noun's gender and number. """
    forms = {"ms": "MS", "fs": "FS", "mp": "MP", "fp": "FP"}
    assert main.describe({"gender": "m", "number": "s"}, forms) == "MS"
    assert main.describe({"gender": "f", "number": "s"}, forms) == "FS"
    assert main.describe({"gender": "m", "number": "p"}, forms) == "MP"
    assert main.describe({"gender": "f", "number": "p"}, forms) == "FP"
    assert main.describe({"gender": "f", "number": "p"}, {"all": "X"}) == "X"


def test_make_name_mixes_polarity():
    """ Both directions come up and the adjective agrees with its noun. """
    words = main.app.config["words"]
    rng = random.Random(1234)
    kinds = set()
    for _ in range(300):
        party = main.make_name(words, rng)
        kinds.add(party["kind"])
        pool = "positive_nouns" if party["kind"] == "positive-negative" else "negative_nouns"
        noun = next(n for n in words[pool] if n["word"] == party["noun"])
        descriptors = words["negative_descriptors" if pool == "positive_nouns" else "positive_descriptors"]
        assert any(main.describe(noun, d) == party["adjective"] for d in descriptors)
        assert party["letters"][0] == party["noun"][0]
        if party["adjective"][0] in main.HEBREW_LETTERS:
            assert party["letters"][1] == party["adjective"][0]
    assert kinds == {"positive-negative", "negative-positive"}


def test_version():
    """ /app/version serves the deploy stamp and the revision. """
    application = webtest.TestApp(main.app)

    response = application.get('/app/version')
    assert response.status_int == 200
    for key in ("deploy_date", "git_describe", "revision"):
        assert key in response.json
