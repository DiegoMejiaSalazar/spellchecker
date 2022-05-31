class NamesDictionary:
    dictionary = dict()

    @staticmethod
    def load():
        with open('names.txt') as file_of_words:
            for word in file_of_words.readlines():
                NamesDictionary.dictionary[word.replace('\n', '')] = True

    @staticmethod
    def word_exist(word):
        try:
            return NamesDictionary.dictionary[word]
        except:
            return False
