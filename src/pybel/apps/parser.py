# -*- coding: utf-8 -*-

"""A simple web-based BEL parser implemented with Flask.

Run from the command line with ``python -m pybel.apps.parser``.
"""

import flask
import pyparsing

import pybel
import pybel.exceptions

app = flask.Flask(__name__)


@app.route('/parse', methods=['POST'])
def parse():
    """Parse the BEL in the `text` JSON field.

    Example usage:

    >>> import requests
    >>> requests.post('http://localhost:5000/parse', json={'text': 'p(HGNC:123) increases p(HGNC:456)'}).json()
    {'input': 'p(HGNC:123) increases p(HGNC:456)', 'output': {'object': {'concept': {'name': '456', 'namespace': 'HGNC'}, 'function': 'Protein'}, 'relation': 'increases', 'subject': {'concept': {'name': '123', 'namespace': 'HGNC'}, 'function': 'Protein'}}, 'success': True}
    """
    text = flask.request.json.get('text')
    if text is None:
        return flask.jsonify(success=False, message='missing `text`')

    try:
        rv = pybel.parse(text)
    except (pyparsing.ParseException, pybel.exceptions.PyBELWarning) as e:
        return flask.jsonify(success=False, input=text, exception=str(e))
    else:
        return flask.jsonify(success=True, input=text, output=rv)


if __name__ == '__main__':
    app.run()
