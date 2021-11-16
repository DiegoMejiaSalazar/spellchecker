from flask import Flask, request
from http import HTTPStatus


app = Flask(__name__)


@app.route('/spell-check', methods=['POST'])
def spell_check():
    if 'file' not in request.files:
        return 'No file part', HTTPStatus.BAD_REQUEST
    print(request.headers.get('start'))
    print(request.headers.get('end'))
    return {"name": "hola"}, HTTPStatus.OK


if __name__ == '__main__':
    app.run()
