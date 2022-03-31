import hunspell
import re
import pdfplumber
from services.dictionary import EnglishDictionary
from services.intersectedwordmodel import IntersercetedWord
from services.namesdictionary import NamesDictionary


diccionario = hunspell.HunSpell('/usr/share/hunspell/esbol.dic',
                              '/usr/share/hunspell/esbol.aff')


def check_if_word_contains_spelling_errors(word):
    return diccionario.spell(word)


def get_suggestions(word):
    return ','.join(map(str, diccionario.suggest(word)))

def generate_intersected_words(list_1, list_2):
    words = [word.get('text') for word in list_2]
    result = []
    positions = [{
        "x1": word.get('x0'),
        "y1": word.get('top'),
        "x2": word.get("x1"),
        "y2": word.get('bottom')
    } for word in list_2]
    for element in list_1:
        if not words.__contains__(element.text):
            continue
        index_of_element = words.index(element.text)
        result.append(IntersercetedWord(element.text,
                                        positions[index_of_element].get("x1"),
                                        positions[index_of_element].get("y1"),
                                        positions[index_of_element].get("x2"),
                                        positions[index_of_element].get("y2"),
                                        element._.get_require_spellCheck,
                                        element._.get_suggestion_spellCheck
                                        )
                      )
        words.remove(element.text)
        positions.pop(index_of_element)
    return result


def analize_file(uploadedFile, nlp):
    words_with_spell_checking_problems = []
    doc = None
    with pdfplumber.open(uploadedFile) as pdf:
        for page in pdf.pages:
            for word in page.extract_words():
                if len(re.findall(r'\w+', word.get('text'))) != 1:
                    continue
                if check_if_word_contains_spelling_errors(re.findall(r'\w+', word.get('text'))[0]):
                    continue
                if EnglishDictionary.word_exist(re.findall(r'\w+', word.get('text'))[0]):
                    continue
                if NamesDictionary.word_exist(re.findall(r'\w+', word.get('text'))[0]):
                    continue
                if re.findall(r'\w+', word.get('text'))[0].isupper():
                    continue
                words_with_spell_checking_problems.append({
                    "text": word.get('text'),
                    "position": {
                        "boundingRect": {
                            "x1": word.get('x0'),
                            "y1": word.get('top'),
                            "x2": word.get("x1"),
                            "y2": word.get('bottom'),
                            "width": page.bbox[2],
                            "height": page.bbox[3]
                        },
                        "pageNumber": page.page_number
                    },
                    "suggestions": get_suggestions(word.get('text')),
                })
    return words_with_spell_checking_problems


def analize_file_with_bert(uploadedFile, nlp):
    words_with_spell_checking_problems = []
    with pdfplumber.open(uploadedFile) as pdf:
        for page in pdf.pages:
            intersected_words = []
            if 6 <= page.page_number <= 10:
                doc = nlp(page.extract_text().replace("\n", " ").replace("  ", " "))
                document_words = page.extract_words()
                intersected_words = generate_intersected_words(doc, document_words)
            for word in intersected_words:
                if len(re.findall(r'\w+', word.text)) != 1:
                    continue
                if check_if_word_contains_spelling_errors(re.findall(r'\w+', word.text)[0]) and not word.has_errors:
                    continue
                if EnglishDictionary.word_exist(re.findall(r'\w+', word.text)[0]):
                    continue
                if NamesDictionary.word_exist(re.findall(r'\w+', word.text)[0]):
                    continue
                if re.findall(r'\w+', word.text)[0].isupper():
                    continue
                words_with_spell_checking_problems.append({
                    "text": word.text,
                    "position": {
                        "boundingRect": {
                            "x1": word.x0,
                            "y1": word.top,
                            "x2": word.y0,
                            "y2": word.bottom,
                            "width": page.bbox[2],
                            "height": page.bbox[3]
                        },
                        "pageNumber": page.page_number
                    },
                    "suggestions": get_suggestions(word.text),
                })
    print("*"*60)
    print(words_with_spell_checking_problems)
    return words_with_spell_checking_problems
