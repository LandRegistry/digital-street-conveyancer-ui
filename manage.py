from flask_script import Manager
from conveyancer_ui.main import app
import os


manager = Manager(app)


@manager.command
def runserver(port=7001):
    """Run the app using flask server"""

    os.environ["PYTHONUNBUFFERED"] = "yes"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["COMMIT"] = "LOCAL"

    app.run(debug=True, port=int(port), ssl_context=('/supporting-files/ssl.cert', '/supporting-files/ssl.key'))


if __name__ == "__main__":
    manager.run()
