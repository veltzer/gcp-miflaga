"""
Miflaga website to generate funny names for political parties in Israel
"""


import json
import os

from flask import Flask, jsonify

app = Flask(__name__)


def load_build_info():
    """ Load the deploy stamp written by gcloud_run_deploy.sh; absent in dev. """
    try:
        with open("build_info.json", encoding="UTF8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {"deploy_date": "unknown", "git_describe": "dev"}


app.config["build_info"] = load_build_info()


@app.route("/")
def index():
    """ root of the site """
    return "<html><body>hello</body></html>"
    # return app.send_static_file("html/index.html")


@app.route("/app/version")
def version():
    """ What is deployed: the deploy stamp plus the serving Cloud Run revision. """
    info = dict(app.config["build_info"])
    # Cloud Run injects the serving revision name at runtime.
    info["revision"] = os.environ.get("K_REVISION", "local")
    return jsonify(info)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
