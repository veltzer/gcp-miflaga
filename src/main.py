"""
Miflaga website to generate funny names for political parties in Israel
"""


from flask import Flask


app = Flask(__name__)

@app.route("/")
def index():
    """ root of the site """
    return "<html><body>hello</body></html>"
    # return app.send_static_file("html/index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
