import hunspell
import re
import pdfplumber
from services.dictionary import EnglishDictionary
from services.namesdictionary import NamesDictionary

diccionario = hunspell.HunSpell('/usr/share/hunspell/esbol.dic',
                              '/usr/share/hunspell/esbol.aff')


def checkIfWordContainsSpellingErrors(word):
    return diccionario.spell(word)

def getSuggestions(word):
    return ','.join(map(str, diccionario.suggest(word)))


def analizeFile(uploadedFile):
    words_with_spell_checking_problems = []
    with pdfplumber.open(uploadedFile) as pdf:
        for page in pdf.pages:
            for word in page.extract_words():
                if len(re.findall(r'\w+', word.get('text'))) != 1:
                    continue
                if checkIfWordContainsSpellingErrors(re.findall(r'\w+', word.get('text'))[0]):
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
                    "suggestions": getSuggestions(word.get('text')),
                })
    return words_with_spell_checking_problems

