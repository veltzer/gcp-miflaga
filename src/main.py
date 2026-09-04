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

from flask import Flask, jsonify, redirect

HERE = os.path.dirname(os.path.abspath(__file__))

# Hebrew letters that may open a word (no final forms), for the ballot code.
HEBREW_LETTERS = "אבגדהוזחטיכלמנסעפצקרשת"

app = Flask(__name__, static_folder="html", static_url_path="/static")


def load_build_info():
    """ Load the deploy stamp written by gcloud_run_deploy.sh; absent in dev. """
    try:
        with open("build_info.json", encoding="UTF8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {"deploy_date": "unknown", "git_describe": "dev"}


def load_words():
    """ Load the Hebrew word bank shipped next to this module. """
    with open(os.path.join(HERE, "data", "words.json"), encoding="UTF8") as fp:
        return json.load(fp)


app.config["build_info"] = load_build_info()
app.config["words"] = load_words()


def describe(noun, descriptor):
    """ The descriptor form that agrees with the noun in gender and number.

    Uninflected phrases ("לכולם") carry a single "all" form.
    """
    if "all" in descriptor:
        return descriptor["all"]
    return descriptor[noun["gender"] + noun["number"]]


def initial(word, rng):
    """ The word's first letter, or a random one when it does not start with a Hebrew letter ("2026"). """
    if word[0] in HEBREW_LETTERS:
        return word[0]
    return rng.choice(HEBREW_LETTERS)


def ballot_letters(noun, adjective, rng):
    """ A ballot code like the real ones: initials, sometimes a third letter. """
    letters = initial(noun, rng) + initial(adjective, rng)
    if rng.random() < 0.5:
        letters += rng.choice(HEBREW_LETTERS)
    return letters


def pick(pool, rng):
    """ A weighted random entry; the weight defaults to 1.

    Words lifted from the names of real parties carry a heavier weight in the
    word bank so that the generated names echo names people recognize.
    """
    return rng.choices(pool, weights=[entry.get("weight", 1) for entry in pool])[0]


def make_name(words, rng=random):
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


@app.route("/")
def index():
    """ root of the site """
    return app.send_static_file("index.html")


@app.route("/favicon.ico")
def favicon():
    """ Browsers ask for this path by default; the icon is an SVG. """
    return redirect("/static/favicon.svg")


@app.route("/app/name")
def name():
    """ One freshly generated party name. """
    return jsonify(make_name(app.config["words"]))


@app.route("/app/version")
def version():
    """ What is deployed: the deploy stamp plus the serving Cloud Run revision. """
    info = dict(app.config["build_info"])
    # Cloud Run injects the serving revision name at runtime.
    info["revision"] = os.environ.get("K_REVISION", "local")
    return jsonify(info)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
