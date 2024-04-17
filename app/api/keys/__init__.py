from flask import Blueprint

bp = Blueprint('keys', __name__)

from app.api.keys import routes