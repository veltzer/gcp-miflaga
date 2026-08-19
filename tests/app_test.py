""" Test the miflaga flask app end to end with webtest. """

import webtest

import main


def test_get():
    """ GET / returns the hello page. """
    application = webtest.TestApp(main.app)

    response = application.get('/')
    assert response.status_int == 200
    assert response.body == b"<html><body>hello</body></html>"
