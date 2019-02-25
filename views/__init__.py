from datetime import datetime

from flask import jsonify

from app import app

@app.route('/version', methods=['GET'])
def version():
    return jsonify({
        "version": "0.1",
        "time_utc": str(datetime.utcnow())
    })

# import all routes in views.py
from . import views
