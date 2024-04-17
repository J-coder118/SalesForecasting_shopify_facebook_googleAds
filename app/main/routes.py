from app.main import bp
from app.db import database as db

@bp.route('/')
def index():
    return 'This is The sales forecasting project'

