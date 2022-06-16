import hunspell
import re
import pdfplumber
from services.dictionary import EnglishDictionary
from services.homologicalwords import HomologicalWords
from services.intersectedwordmodel import IntersercetedWord
from services.namesdictionary import NamesDictionary
import torch
import math
import time

diccionario = hunspell.HunSpell('/usr/share/hunspell/esbol.dic',
                              '/usr/share/hunspell/esbol.aff')


def check_if_word_contains_spelling_errors(word):
    return diccionario.spell(word)


def format_suggestions(suggestions):
    return ','.join(map(str, suggestions))


def mask_paragraph(paragraph):
    for word in HomologicalWords.words:
        paragraph = paragraph.replace(" " + word + " ", " [MASK] ")
        paragraph = paragraph.replace(" " + word + ",", " [MASK],")
        paragraph = paragraph.replace(" " + word + ".", " [MASK].")
        paragraph = paragraph.replace(" " + word + ":", " [MASK]:")
    return paragraph


def get_mask_positions(tokenized_paragraph):
    result = []
    counter = 0
    for element in tokenized_paragraph:
        if element == 0:
            result.append(counter)
        counter += 1
    return result


def has_contextual_errors(original_word, predictions):
    if len(predictions) == 0 or original_word in predictions:
        return False
    return True


def check_if_paragraph_contains_list_of_words(list_of_words, paragraph):
    for word in list_of_words:
        if re.search(r'\b{0}\b'.format(word), paragraph):
            return True
    return False


def sentence_contains_homological_word(list_of_words, sentence):
    for word in list_of_words:
        if re.search(r'\b{0}\b'.format(word), sentence):
            return word, True
    return None, False


def get_sentences_with_contextual_errors(paragraph):
    result = []
    splitted_paragraph = paragraph.split('\n')
    sentence_to_add = ''
    sentence_before = ''
    word_with_homological_error = ''
    is_inside_pdf_table = False
    sentence_before_was_added = False
    is_pending_to_add = False
    for sentence in splitted_paragraph:
        if re.search(r'\bTabla\b\s\d', sentence):
            is_inside_pdf_table = True
        if re.search(r'\b[f,F]uente\b\s*[:]', sentence):
            is_inside_pdf_table = False
        analized_word, has_error = sentence_contains_homological_word(HomologicalWords.words, sentence)
        if (not has_error) and not sentence_before_was_added:
            if sentence == '':
                continue
            sentence_before = sentence
            continue
        if has_error:
            word_with_homological_error = analized_word
            sentence_to_add += sentence_before + " " + sentence + " "
            sentence_before_was_added = True
            is_pending_to_add = True
            continue
        if (not has_error) and sentence_before_was_added:
            if sentence == '':
                continue
            sentence_to_add += sentence
            splitted_sentence = re.split(r'\W+',sentence_to_add)
            result.append((is_inside_pdf_table, [x for x in splitted_sentence if x in HomologicalWords.words], sentence_to_add))
            sentence_before_was_added = False
            is_pending_to_add = False
            sentence_to_add = ''
            sentence_before = ''
    if is_pending_to_add:
        splitted_sentence = re.split(r'\W+',sentence_to_add)
        result.append((is_inside_pdf_table,  [x for x in splitted_sentence if x in HomologicalWords.words], sentence_to_add))
    return result


def generate_intersected_words(extracted_text, extracted_words, model, tokenizer):
    result = []
    splitted_paragraphs = extracted_text.split("\n\n")
    paragraphs_with_homological_words = [paragraph for paragraph in splitted_paragraphs if check_if_paragraph_contains_list_of_words(HomologicalWords.words, paragraph)]
    predicted_token = []
    first_homological_word_in_pair = False
    words_in_sentence_with_homological_erorrs = []
    previous_word = ''
    # print("======================================= FIRST PART ============================")
    for paragraph in paragraphs_with_homological_words:
        sentences_containing_contextual_errors = get_sentences_with_contextual_errors(paragraph)
        for is_inside_pdf_table, word, sentence in sentences_containing_contextual_errors:
            masked_paragraph = mask_paragraph("[CLS] " + sentence + " [SEP]")
            tokens = tokenizer.tokenize(masked_paragraph)
            indexed_tokens = tokenizer.convert_tokens_to_ids(tokens)
            mask_positions = get_mask_positions(indexed_tokens)
            tokens_tensor = torch.tensor([indexed_tokens])
            predictions = model(tokens_tensor)[0]
            loss_fct = torch.nn.CrossEntropyLoss()
            loss = loss_fct(predictions.squeeze(), tokens_tensor.squeeze()).data
            # print("LOSS: ", math.exp(loss))
            # print("SENTENCE: ", sentence)
            print("WORDS: ", word)
            # print("MASKED PARAGRAPH: ", masked_paragraph)
            # print("IS INSIDE PDF TABLE", is_inside_pdf_table)
            if len(mask_positions) == 1:
                idxs = torch.argsort(predictions[0, mask_positions[0]], descending=True)
                print("PREDICTIONS 1: ", tokenizer.convert_ids_to_tokens(idxs[:5]))
                predicted_token.append((is_inside_pdf_table,word[0], tokenizer.convert_ids_to_tokens(idxs[:5]), math.exp(loss)))
            else:
                for i, midx in enumerate(mask_positions):
                    idxs = torch.argsort(predictions[0, midx], descending=True)
                    # print("PREDICTIONS 2: ", tokenizer.convert_ids_to_tokens(idxs[:5]))
                    # print("ADDING === ", (is_inside_pdf_table, word[i], tokenizer.convert_ids_to_tokens(idxs[:5]), math.exp(loss)))
                    predicted_token.append((is_inside_pdf_table, word[i], tokenizer.convert_ids_to_tokens(idxs[:5]), math.exp(loss)))
            # print("-" * 100)
    # print(predicted_token)
    # print("===================================== SECOND PART =============================================")
    for word in extracted_words:
        word_to_analize = word.get('text')
        if ':' in word_to_analize or '.' in word_to_analize or ',' in word_to_analize:
            word_to_analize = word_to_analize.replace(':', '').replace(',', '').replace('.', '')
        if word_to_analize in HomologicalWords.words:
            print('WORDDD ->', word_to_analize)
            # print("word in second part: ", word_to_analize)
            if previous_word in HomologicalWords.words:
                # print("two homologica words in one")
                # print("!!!!!!!!!!!!! WORD was being pop in sequence")
                predicted_token.pop(0)
                # print('word 1: ', previous_word)
                # print('word 2: ', word_to_analize)
                # print('PREDICTED TOKENS: ', predicted_token)
                # print('RESULT ===================================')
                # for e in result:
                #     print("PREDICTION : ", e.text, " SUGGESTION: ", e.suggestions)
                previous_word = word_to_analize
                # print('FINISH RESULT ===================================')
                continue
            previous_word = word_to_analize
            if len(predicted_token) == 0:
                # print("THIS SHOULD NOT HAPPEN !!!!!!!!!!!!!!!!!")
                continue
            is_in_contained_in_table, word_with_errors, homological_predictions, loss_value = predicted_token[0]
            if word_to_analize != word_with_errors:
                continue
            else:
                is_in_contained_in_table, word_with_errors, homological_predictions, loss_value = predicted_token.pop(0)
            # print("WORD IS BEING POPPED!!! -> ", word_with_errors)
            if word_with_errors in homological_predictions:
                # print("WORD WAS DISCARTED -> ", word_with_errors)
                continue
            else:
                if loss_value > 5:
                    first_homological_word_in_pair = False
                    # print("WORD WAS DISCARTED -> ", word_with_errors)
                    continue
                if is_in_contained_in_table:
                    first_homological_word_in_pair = False
                    # print("WORD WAS DISCARTED DUE TO IT IS CONTAINED INSIDE PDF TABLE -> ", word_with_errors)
                    continue
            if word_with_errors == 'concejo':
                homological_predictions = ['consejo']
            if word_with_errors == 'consejo':
                homological_predictions = ['concejo']
            homological_predictions = [w for w in homological_predictions if check_if_word_contains_spelling_errors(w)]
            intersected_word_to_append = IntersercetedWord(word_to_analize, word.get('x0'), word.get('top'), word.get("x1"), word.get('bottom'), has_contextual_errors(word_to_analize, homological_predictions), False, format_suggestions(homological_predictions))
            result.append(intersected_word_to_append)
            first_homological_word_in_pair = True
            continue
        if not check_if_word_contains_spelling_errors(word_to_analize):
            regexed_word = re.findall(r'\w+', word.get('text'))
            if len(regexed_word) == 0:
                continue
            first_homological_word_in_pair = False
            previous_word = word_to_analize
            if EnglishDictionary.word_exist(regexed_word[0]):
                continue
            if NamesDictionary.word_exist(regexed_word[0]):
                continue
            if regexed_word[0].isupper():
                continue
            intersected_word_to_append = IntersercetedWord(word_to_analize, word.get('x0'), word.get('top'), word.get("x1"), word.get('bottom'), False, True, get_spelling_suggestions(word_to_analize))
            result.append(intersected_word_to_append)
        previous_word = word_to_analize
    return result


def analize_file(uploadedFile, nlp):
    words_with_spell_checking_problems = []
    with pdfplumber.open(uploadedFile) as pdf:
        for page in pdf.pages:
            for word in page.extract_words():
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
                    "suggestions": word.suggestions,
                })
    return words_with_spell_checking_problems


def add_spaces_to_word(word):
    return " " + word + " "


def get_spelling_suggestions(word):
    return diccionario.suggest(word)


def check_if_contains_homological_words(text):
    return any(add_spaces_to_word(substring) in text for substring in HomologicalWords.words)


def get_type_of_misspelling(intersectedwordmodel):
    if not intersectedwordmodel.is_ortographical_error:
        return 'contextual'
    return 'ortografia'


def analize_file_with_bert(uploadedFile, model, tokenizer):
    start_time = time.time()
    words_with_spell_checking_problems = []
    with pdfplumber.open(uploadedFile) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if not check_if_contains_homological_words(extracted_text.replace("\n", " ")):
                continue
            document_words = page.extract_words()
            intersected_words = generate_intersected_words(extracted_text, document_words, model, tokenizer)
            for word in intersected_words:
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
                    "suggestions": word.suggestions,
                })
    print('============================= TIME TOOK ============================')
    print("--- %s seconds ---" % (time.time() - start_time))
    return words_with_spell_checking_problems
