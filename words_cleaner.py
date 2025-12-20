from spellchecker import SpellChecker

spell = SpellChecker()

def check_word(word):
    # known() returns the word if it exists in the dictionary
    return spell.known([word.lower()])

words = [word.strip() for word in open("words.txt").readlines()]

for word in words:
    if check_word(word): print(word)