from flask import Flask, request
from http import HTTPStatus
from services.namesdictionary import NamesDictionary
from services.spellcheckerservice import analize_file_with_bert
from services.dictionary import EnglishDictionary
from transformers import BertForMaskedLM, BertTokenizer
from waitress import serve
import sys

tokenizer = BertTokenizer.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
model = BertForMaskedLM.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
app = Flask(__name__)


@app.route('/spell-check', methods=['POST'])
def spell_check():
    if 'file' not in request.files:
        return 'No file part', HTTPStatus.BAD_REQUEST
    bibliography_index = int(request.args.to_dict().get('bibliographystart'))
    if bibliography_index == 0:
        bibliography_index = sys.maxint
    return {"errors": analize_file_with_bert(request.files['file'], model, tokenizer, bibliography_index)}, HTTPStatus.OK


if __name__ == '__main__':
    EnglishDictionary.load()
    NamesDictionary.load()
    serve(app, host="0.0.0.0", port=5000)
    print('app is serving on localhost:5000')
