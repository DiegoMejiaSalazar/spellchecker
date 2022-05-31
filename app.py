from flask import Flask, request
from http import HTTPStatus
import spacy
from services.namesdictionary import NamesDictionary
from services.spellcheckerservice import analize_file_with_bert
from services.dictionary import EnglishDictionary
from transformers import BertForMaskedLM, BertTokenizer

tokenizer = BertTokenizer.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
model = BertForMaskedLM.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
app = Flask(__name__)


@app.route('/spell-check', methods=['POST'])
def spell_check():
    if 'file' not in request.files:
        return 'No file part', HTTPStatus.BAD_REQUEST
    return {"errors": analize_file_with_bert(request.files['file'], model, tokenizer)}, HTTPStatus.OK


if __name__ == '__main__':
    EnglishDictionary.load()
    NamesDictionary.load()
    app.run()
