# Import every blueprint file
from conveyancer_ui.views import general, index, conveyancer_admin, conveyancer_user, login


def register_blueprints(app):
    """Adds all blueprint objects into the app."""
    app.register_blueprint(general.general)
    app.register_blueprint(index.index)
    app.register_blueprint(conveyancer_admin.admin, url_prefix="/admin")
    app.register_blueprint(conveyancer_user.user, url_prefix="/user")
    app.register_blueprint(login.login)

    # All done!
    app.logger.info("Blueprints registered")
