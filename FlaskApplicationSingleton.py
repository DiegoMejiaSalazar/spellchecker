from flask import Flask


class FlaskApplication:

    __application = Flask(__name__)

    @staticmethod
    def get_application():
        return FlaskApplication.__application