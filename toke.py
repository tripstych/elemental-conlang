import nltk
from nltk import pos_tag
from nltk.tokenize import word_tokenize


def simplify_tag(treebank_tag):
    return treebank_tag
    if treebank_tag.startswith('NN'):
        return 'N'
    if treebank_tag.startswith('VB'):
        return 'V'
    if treebank_tag.startswith('JJ'):
        return 'ADJ'
    if treebank_tag.startswith('RB'):
        return 'ADV'
    if treebank_tag in {'PRP', 'PRP$', 'WP', 'WP$'}:
        return 'PRON'
    if treebank_tag in {'DT', 'WDT', 'PDT'}:
        return 'DET'
    if treebank_tag in {'IN', 'TO'}:
        return 'PREP'
    if treebank_tag in {'CC'}:
        return 'CONJ'
    if treebank_tag in {'CD'}:
        return 'NUM'
    if treebank_tag in {'.', ',', ':', '``', "''", '-LRB-', '-RRB-'}:
        return 'PUNCT'
    return treebank_tag


def show_tokens(text):
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)
    return " ".join(f"[{simplify_tag(tag)}] {tok}" for tok, tag in tagged)


if __name__ == '__main__':
    while True:
        line = input('> ').strip()
        if not line or line.lower() == 'quit':
            break
        print(show_tokens(line))
