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


@app.route('/spell-check', methods = ["POST"])
def spell_check():
    if 'file' not in request.files:
        return 'No file part', HTTPStatus.BAD_REQUEST
    bibliography_index = int(request.args.to_dict().get('bibliographystart'))
    figure_index = int(request.args.to_dict().get('figureIndexEndPage'))
    general_index = int(request.args.to_dict().get('generalIndexEndPage')) 
    table_index = int(request.args.to_dict().get('tableIndexEndPage'))
    print("bibliography index: ", bibliography_index)
    print("figure index: ", figure_index)
    print("general index: ", general_index)
    print("table index: ", table_index)
    max_amount_of_homologicals_to_check = 10
    if bibliography_index == 0:
        bibliography_index = sys.maxsize
    # return {"errors": analize_file_with_bert(request.files['file'], model, tokenizer, bibliography_index)}, HTTPStatus.OK
    max_index_page = max([figure_index, general_index, table_index]) + 1
    return {"errors": analize_file_with_bert(request.files['file'], model, tokenizer, bibliography_index, max_index_page, max_amount_of_homologicals_to_check)}, HTTPStatus.OK

if __name__ == '__main__':
    EnglishDictionary.load()
    NamesDictionary.load()
    serve(app, host="0.0.0.0", port=5000)
    print('app is serving on localhost:5000')
