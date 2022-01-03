class EnglishDictionary:
    dictionary = dict()

    @staticmethod
    def load():
        print("hello")
        with open('words.txt') as file_of_words:
            for word in file_of_words.readlines():
                if word.find("-") != -1:
                    continue
                if word[:len(word) - 2].__contains__("microsoft"):
                    print("Adding microsoft")
                EnglishDictionary.dictionary[word[:len(word) - 1]] = True

    @staticmethod
    def check_if_word_exist(word):
        try:
            return EnglishDictionary.dictionary[word]
        except:
            return False

    @staticmethod
    def word_exist(word):
        if word == "Microsoft":
            print("lheey")
        return EnglishDictionary.check_if_word_exist(word.lower()) or EnglishDictionary.check_if_word_exist(word)
