from flask import Flask, request
from http import HTTPStatus

from services.namesdictionary import NamesDictionary
from services.spellcheckerservice import analizeFile
from services.dictionary import EnglishDictionary


app = Flask(__name__)



@app.route('/spell-check', methods=['POST'])
def spell_check():
    if 'file' not in request.files:
        return 'No file part', HTTPStatus.BAD_REQUEST
    return {"errors": analizeFile(request.files['file'])}, HTTPStatus.OK


if __name__ == '__main__':
    EnglishDictionary.load()
    NamesDictionary.load()
    app.run()
