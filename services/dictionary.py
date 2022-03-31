class EnglishDictionary:
    dictionary = dict()

    @staticmethod
    def load():
        with open('words.txt') as file_of_words:
            for word in file_of_words.readlines():
                if word.find("-") != -1:
                    continue
                EnglishDictionary.dictionary[word[:len(word) - 1]] = True

    @staticmethod
    def check_if_word_exist(word):
        try:
            return EnglishDictionary.dictionary[word]
        except:
            return False

    @staticmethod
    def word_exist(word):
        return EnglishDictionary.check_if_word_exist(word.lower()) or EnglishDictionary.check_if_word_exist(word)
