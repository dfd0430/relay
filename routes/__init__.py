from .main_routes import register_main_routes
from .db_routes import register_db_routes
from .obda_routes import register_obda_routes
from .random_routes import register_random_routes
from .logic_routes import register_logic_routes
from .manage_routes import register_manage_routes
from .deploy_routes import register_deploy_routes

def register_routes(app, db):
    register_main_routes(app, db)
    register_db_routes(app, db)
    register_obda_routes(app, db)
    register_random_routes(app, db)
    register_logic_routes(app, db)
    register_manage_routes(app, db)
    register_deploy_routes(app, db)
