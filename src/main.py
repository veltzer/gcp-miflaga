"""
Miflaga website to generate funny names for political parties in Israel
"""


import flask


app = flask.Flask(__name__)

# this route is not needed in production
@app.route("/", methods=["GET"])
def index():
    """ root of the site """
    return app.send_static_file("html/index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
