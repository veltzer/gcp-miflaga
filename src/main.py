"""
Miflaga website to generate funny names for political parties in Israel

A party name is a noun plus a descriptor, where one is positive and the
other negative: "תקווה מוגבלת" (limited hope) or "מיסים נצחיים" (eternal
taxes). Hebrew adjectives agree with the noun in gender and number, so the
word bank (src/data/words.json) carries that information and the generator
picks the matching form.
"""


import json
import os
import random
import urllib.parse
from typing import TYPE_CHECKING, Any

from flask import Flask, jsonify, redirect, request

if TYPE_CHECKING:
    from werkzeug.wrappers.response import Response

# The generator behind every served name; tests pass a seeded one instead.
RNG = random.Random()

HERE = os.path.dirname(os.path.abspath(__file__))
# build_info.json is written next to src/, at the repo (and image) root.
BUILD_INFO = os.path.join(os.path.dirname(HERE), "build_info.json")

# Hebrew letters that may open a word (no final forms), for the ballot code.
HEBREW_LETTERS = "אבגדהוזחטיכלמנסעפצקרשת"

app = Flask(__name__, static_folder="html", static_url_path="/static")


def load_build_info():
    """ Load the deploy stamp written by gcloud_deploy.sh; absent in dev. """
    try:
        with open(BUILD_INFO, encoding="UTF8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {"deploy_date": "unknown", "git_describe": "dev"}


def load_words():
    """ Load the Hebrew word bank shipped next to this module. """
    with open(os.path.join(HERE, "data", "words.json"), encoding="UTF8") as fp:
        return json.load(fp)


app.config["build_info"] = load_build_info()
app.config["words"] = load_words()
# The one hostname the site is served on (gcp_domain in .gcp.conf); empty in
# dev, where the app answers on whatever host it is reached on.
app.config["canonical_host"] = os.environ.get("CANONICAL_HOST", "")


def describe(noun: dict[str, str], descriptor: dict[str, str]) -> str:
    """ The descriptor form that agrees with the noun in gender and number.

    Uninflected phrases ("לכולם") carry a single "all" form.
    """
    if "all" in descriptor:
        return descriptor["all"]
    return descriptor[noun["gender"] + noun["number"]]


def initial(word: str, rng: random.Random) -> str:
    """ The word's first letter, or a random one when it does not start with a Hebrew letter ("2026"). """
    if word[0] in HEBREW_LETTERS:
        return word[0]
    return rng.choice(HEBREW_LETTERS)


def ballot_letters(noun: str, adjective: str, rng: random.Random) -> str:
    """ A ballot code like the real ones: initials, sometimes a third letter. """
    letters = initial(noun, rng) + initial(adjective, rng)
    if rng.random() < 0.5:
        letters += rng.choice(HEBREW_LETTERS)
    return letters


def pick(pool: list[dict[str, Any]], rng: random.Random):
    """ A weighted random entry; the weight defaults to 1.

    Words lifted from the names of real parties carry a heavier weight in the
    word bank so that the generated names echo names people recognize.
    """
    return rng.choices(pool, weights=[entry.get("weight", 1) for entry in pool])[0]


def make_name(words: dict[str, list[dict[str, Any]]], rng: random.Random = RNG):
    """ Generate one party name from the word bank. """
    if rng.random() < 0.5:
        kind = "positive-negative"
        noun = pick(words["positive_nouns"], rng)
        descriptor = pick(words["negative_descriptors"], rng)
    else:
        kind = "negative-positive"
        noun = pick(words["negative_nouns"], rng)
        descriptor = pick(words["positive_descriptors"], rng)
    adjective = describe(noun, descriptor)
    return {
        "noun": noun["word"],
        "adjective": adjective,
        "name": f"{noun['word']} {adjective}",
        "letters": ballot_letters(noun["word"], adjective, rng),
        "kind": kind,
    }


@app.before_request
def redirect_to_canonical_host() -> Response | None:
    """ Send every other hostname to the canonical one, path and query kept.

    The service is also reached on its run.app hostnames and on
    miflaga.veltzer.org (see doc/addresses.md). /app/version is exempt, so
    the deploy stamp can still be asked of each address directly.
    """
    host = app.config["canonical_host"]
    if not host or request.host == host or request.path == "/app/version":
        return None
    url = urllib.parse.urlsplit(request.url)._replace(scheme="https", netloc=host).geturl()
    return redirect(url, code=308)


@app.route("/")
def index() -> Response:
    """ root of the site """
    return app.send_static_file("index.html")


@app.route("/favicon.ico")
def favicon() -> Response:
    """ Browsers ask for this path by default; the icon is an SVG. """
    return redirect("/static/favicon.svg")


@app.route("/app/name")
def name() -> Response:
    """ One freshly generated party name. """
    return jsonify(make_name(app.config["words"]))


@app.route("/app/version")
def version() -> Response:
    """ What is deployed: the deploy stamp plus the serving Cloud Run revision. """
    info = dict(app.config["build_info"])
    # Cloud Run injects the serving revision name at runtime.
    info["revision"] = os.environ.get("K_REVISION", "local")
    return jsonify(info)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
