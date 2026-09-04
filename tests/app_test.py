""" Test the miflaga flask app end to end with webtest. """

import webtest

import main


def test_get():
    """ GET / returns the hello page. """
    application = webtest.TestApp(main.app)

    response = application.get('/')
    assert response.status_int == 200
    assert response.body == b"<html><body>hello</body></html>"


def test_version():
    """ /app/version serves the deploy stamp and the revision. """
    application = webtest.TestApp(main.app)

    response = application.get('/app/version')
    assert response.status_int == 200
    for key in ("deploy_date", "git_describe", "revision"):
        assert key in response.json
