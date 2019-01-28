# This file is the entry point.
# First we import the app object, which will get initialised as we do it. Then import methods we're about to use.
from conveyancer_ui.app import app
from conveyancer_ui.blueprints import register_blueprints
from conveyancer_ui.exceptions import register_exception_handlers
from conveyancer_ui.extensions import register_extensions

# Now we register any extensions we use into the app
register_extensions(app)
# Register the exception handlers
register_exception_handlers(app)
# Finally we register our blueprints to get our routes up and running.
register_blueprints(app)
