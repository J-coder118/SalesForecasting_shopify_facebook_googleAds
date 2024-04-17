from flask import Blueprint

bp = Blueprint('sales', __name__)


from app.api.sales import routes