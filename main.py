import bisect
import os
import json
import flask


# the app object
app = flask.Flask(__name__, static_url_path='')

# this route is not needed in production
@app.route('/', methods=['GET'])
def index():
    return app.send_static_file("html/index.html")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False)
