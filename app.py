from flask import Flask, request
from http import HTTPStatus
import spacy
from services.contextualspellchecker import ContextualSpellCheck

from services.namesdictionary import NamesDictionary
from services.spellcheckerservice import analize_file_with_bert
from services.dictionary import EnglishDictionary
import torch
from transformers import BertForMaskedLM, BertTokenizer

tokenizer = BertTokenizer.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
model = BertTokenizer.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
app = Flask(__name__)



def load_spacy_contextual():
    print("Code running...")
    nlp = spacy.load("es_dep_news_trf")
    if "parser" not in nlp.pipe_names:
        raise AttributeError(
            "parser is required please enable it in nlp pipeline"
        )
    nlp.add_pipe(
        "contextual spellchecker", config={"debug": False, "max_edit_dist": 7}
    )
    return nlp


nlp = load_spacy_contextual()


@app.route('/spell-check', methods=['POST'])
def spell_check():
    if 'file' not in request.files:
        return 'No file part', HTTPStatus.BAD_REQUEST
    return {"errors": analize_file_with_bert(request.files['file'], model, tokenizer)}, HTTPStatus.OK


if __name__ == '__main__':
    EnglishDictionary.load()
    NamesDictionary.load()
    app.run()
