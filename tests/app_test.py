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
    for key in ("positive_descriptors", "negative_descriptors"):
        assert words[key]
        for descriptor in words[key]:
            if "all" in descriptor:
                assert set(descriptor) == {"all"}
            else:
                assert set(descriptor) == {"ms", "fs", "mp", "fp"}
            assert all(descriptor.values())


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
        assert party["letters"][1] == party["adjective"][0]
    assert kinds == {"positive-negative", "negative-positive"}


def test_version():
    """ /app/version serves the deploy stamp and the revision. """
    application = webtest.TestApp(main.app)

    response = application.get('/app/version')
    assert response.status_int == 200
    for key in ("deploy_date", "git_describe", "revision"):
        assert key in response.json
