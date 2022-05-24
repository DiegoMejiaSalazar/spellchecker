import hunspell
import re
import pdfplumber
from services.dictionary import EnglishDictionary
from services.homologicalwords import HomologicalWords
from services.intersectedwordmodel import IntersercetedWord
from services.namesdictionary import NamesDictionary
import torch


diccionario = hunspell.HunSpell('/usr/share/hunspell/esbol.dic',
                              '/usr/share/hunspell/esbol.aff')


def check_if_word_contains_spelling_errors(word):
    return diccionario.spell(word)


def get_suggestions(word):
    if word.is_contextual_error:
        return word.suggestions
    return ','.join(map(str, diccionario.suggest(word)))


def mask_paragraph(paragraph):
    for word in HomologicalWords.words:
        paragraph = paragraph.replace(" " + word + " ", " [MASK] ")
    return paragraph


def get_mask_positions(tokenized_paragraph):
    result = []
    counter = 0
    for element in tokenized_paragraph:
        if element == 0:
            result.append(counter)
        counter += 1
    return result


def generate_intersected_words(extracted_text, extracted_words, model, tokenizer):
    result = []
    # words_with_contextual_errors = [{'text': word.text, 'suggestion': word._.get_suggestion_spellCheck} for word in list_1 if HomologicalWords.words.__contains__(word.text)]
    # for word in list_2:
    #     if not any(x for x in words_with_contextual_errors if x['text'] == word.get('text')):
    #         continue
    #     contextual_suggestion = next(x for x in words_with_contextual_errors if x['text'] == word.get('text'))['suggestion']
    #     if contextual_suggestion == '' or contextual_suggestion == word.get('text'):
    #         word_has_contexl_error = False
    #     else:
    #         word_has_contexl_error = True
    #     result.append(IntersercetedWord(word.get('text'),
    #                                     word.get('x0'),
    #                                     word.get('top'),
    #                                     word.get("x1"),
    #                                     word.get('bottom'),
    #                                     word_has_contexl_error,
    #                                     False,
    #                                     contextual_suggestion
    #                                     )
    #                   )
    #     if len(words_with_contextual_errors) > 0:
    #         words_with_contextual_errors.pop(0)
    splitted_paragraphs = extracted_text.split("\n")
    paragraphs_with_homological_words = [paragraph for paragraph in splitted_paragraphs if any(add_spaces_to_word(text) in paragraph for text in HomologicalWords.words)]
    for paragraph in paragraphs_with_homological_words:
        masked_paragraph = mask_paragraph("[CLS] " + paragraph + " [SEP]")
        tokens = tokenizer.tokenize(masked_paragraph)
        indexed_tokens = tokenizer.convert_tokens_to_ids(tokens)
        tokens_tensor = torch.tensor([indexed_tokens])
        mask_positions = get_mask_positions(indexed_tokens)
        predictions = model(tokens_tensor)[0]
        if len(mask_positions) == 1:
            idxs = torch.argsort(predictions[0, mask_positions[0]], descending=True)
            predicted_token = tokenizer.convert_ids_to_tokens(idxs[:5])
        else:
            for i, midx in enumerate(mask_positions):
                idxs = torch.argsort(predictions[0, midx], descending=True)
                predicted_token = tokenizer.convert_ids_to_tokens(idxs[:5])
    return result


def analize_file(uploadedFile, nlp):
    words_with_spell_checking_problems = []
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
                    "suggestions": get_suggestions(word),
                })
    return words_with_spell_checking_problems


def add_spaces_to_word(word):
    return " " + word + " "


def check_if_contains_homological_words(text):
    return any(add_spaces_to_word(substring) in text for substring in HomologicalWords.words)


def get_type_of_misspelling(intersectedwordmodel):
    if intersectedwordmodel.is_contextual_error and intersectedwordmodel.is_ortographical_error is False:
        return 'contextual'
    if intersectedwordmodel.is_contextual_error is False and intersectedwordmodel.is_ortographical_error:
        return 'ortografia'
    print('it seems that the word ', intersectedwordmodel.text, ' has both errors')
    return 'unknown'


def analize_file_with_bert(uploadedFile, model, tokenizer):
    words_with_spell_checking_problems = []
    with pdfplumber.open(uploadedFile) as pdf:
        for page in pdf.pages:
            # cleaned_text_for_checking_homological_words = page.extract_text().replace("\n", " ")\
            #     .replace(".", " ")\
            #     .replace(",", " ")\
            #     .replace("(", " ")\
            #     .replace(")", " ")\
            #     .replace("?", " ")\
            #     .replace("¿", " ")\
            #     .replace("!", " ")
            extracted_text = page.extract_text()
            if not check_if_contains_homological_words(extracted_text):
                continue
            # intersected_words = analized_text[0]
            # doc = nlp(intersected_words)
            document_words = page.extract_words()
            intersected_words = generate_intersected_words(extracted_text, document_words, model, tokenizer)
            for word in intersected_words:
                if len(re.findall(r'\w+', word.text)) != 1:
                    continue
                if check_if_word_contains_spelling_errors(re.findall(r'\w+', word.text)[0]) and not word.is_contextual_error and not word.is_ortographical_error:
                    continue
                if EnglishDictionary.word_exist(re.findall(r'\w+', word.text)[0]):
                    continue
                if NamesDictionary.word_exist(re.findall(r'\w+', word.text)[0]):
                    continue
                if re.findall(r'\w+', word.text)[0].isupper():
                    continue
                words_with_spell_checking_problems.append({
                    "text": word.text,
                    "type": get_type_of_misspelling(word),
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
                    "suggestions": get_suggestions(word),
                })
    print("*"*60)
    print(words_with_spell_checking_problems)
    return words_with_spell_checking_problems
