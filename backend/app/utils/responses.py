from flask import jsonify


def ok(data=None, status_code: int = 200):
    """Consistent success envelope: {"data": ...}"""
    return jsonify({"data": data if data is not None else {}}), status_code
