import sys
import argparse
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from num2words import num2words
import yoda
import json
import os
import re

# --- NLTK SETUP (Run once) ---
# nltk.download('punkt')
# nltk.download('averaged_percept1ron_tagger')
# nltk.download('wordnet')
# nltk.download('omw-1.4')
# nltk.download('punkt_tab')

"""Translator for conlang_lexicon.json.

Lexicon values can be either:
- dict (new format): {"word": "...", "composition": {...}, ...}
- str  (legacy format): "..."
"""

class ConlangTranslator:
    """English -> conlang translator using a WordNet-style keyed lexicon."""

    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.lemmatizer = WordNetLemmatizer()

    @staticmethod
    def get_wordnet_pos(treebank_tag):
        """Map NLTK POS tags to WordNet POS tags."""
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        if treebank_tag.startswith('V'):
            return wordnet.VERB
        if treebank_tag.startswith('N'):
            return wordnet.NOUN
        if treebank_tag.startswith('R'):
            return wordnet.ADV
        return wordnet.NOUN

    @staticmethod
    def entry_to_word(entry, fallback):
        """Extract a surface form from a lexicon entry."""
        if isinstance(entry, dict):
            return entry.get('word', fallback)
        if isinstance(entry, str):
            return entry
        return fallback

    def find_best_key(self, lemma, wn_pos):
        """Find the best matching key in the lexicon for lemma/POS."""
        # Priority 1: Exact Match (lemma + pos + .01)
        candidate_01 = f"{lemma}.{wn_pos}.01"
        if candidate_01 in self.lexicon:
            return candidate_01

        # Priority 2: Fuzzy Match (lemma + pos)
        prefix = f"{lemma}.{wn_pos}."
        for key in self.lexicon:
            if key.startswith(prefix):
                return key

        # Priority 3: Desperation Match (lemma only)
        prefix = f"{lemma}."
        for key in self.lexicon:
            if key.startswith(prefix):
                return key

        return None

    def translate_sentence(self, sentence):
        """Translate a sentence; unknown words are output as [word]."""
        sentence = re.sub(r"\d+", lambda x: num2words(int(x.group(0))  ), sentence)
        sentence = sentence.replace("-"," ")
        
        
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        def translate_token(word, tag):
            wn_pos = self.get_wordnet_pos(tag)
            lemma = self.lemmatizer.lemmatize(word.lower(), pos=wn_pos)

            target_key = self.find_best_key(lemma, wn_pos)
            if target_key and target_key in self.lexicon:
                return self.entry_to_word(self.lexicon[target_key], f"[{word}]")
            return f"[{word}]"

        translation = []
        i = 0
        while i < len(tagged):
            word, tag = tagged[i]

            # Pass through punctuation
            if not word.isalnum():
                translation.append(word)
                i += 1
                continue

            # Flip participle-before-noun pairs: "running man" -> "man running"
            if tag in {'VBG', 'VBN'} and i + 1 < len(tagged):
                next_word, next_tag = tagged[i + 1]
                if next_word.isalnum() and next_tag.startswith('NN'):
                    translation.append(translate_token(next_word, next_tag))
                    translation.append(translate_token(word, tag))
                    i += 2
                    continue

            translation.append(translate_token(word, tag))
            i += 1

        return " ".join(translation)

    @classmethod
    def from_json(cls, filename):
        """Load a lexicon JSON file and return a translator."""
        with open(filename, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        return cls(lexicon)


def _configure_utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def _load_translator(lexicon_path):
    if not os.path.exists(lexicon_path):
        raise FileNotFoundError(lexicon_path)
    translator = ConlangTranslator.from_json(lexicon_path)
    return translator


def _detect_convo_path(base_dir):
    for candidate in ('convo.csv', 'convo..csv'):
        p = os.path.join(base_dir, candidate)
        if os.path.exists(p):
            return p
    return None


def _read_convo_sentences(convo_path):
    with open(convo_path, 'r', encoding='utf-8') as f:
        sentences = []
        for line in f:
            match = re.search(r"'((?:\\'|[^'])*)'", line)
            if not match:
                continue
            sentence = match.group(1).replace("\\'", "'").strip()
            if sentence:
                sentences.append(sentence)
    return sentences


def run_auto(translator, convo_path, output_path):
    sentences = _read_convo_sentences(convo_path)

    with open(output_path, "w", encoding="utf-8") as f:
        last = ""
        print("-" * 50)
        for set in sentences:
            if last == set:
                continue
            test = set.split('.')
            if len(test) > 1:
                for myset in test:
                    if last == myset:
                        continue
                    out = translator.translate_sentence(set)
                continue
            out = translator.translate_sentence(set)
            if out == last:
                continue
            print(out)
            f.write(out + "\n")
            f.flush()
            last = out
            #time.sleep(1)


def run_interactive(translator, output_path=None, yoda_mode=False):
    f = None
    if output_path:
        f = open(output_path, "a", encoding="utf-8")
    try:
        print("Type English to translate. Blank line or 'quit' to exit.")
        while True:
            try:
                line = input('> ')
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line.strip() or line.strip().lower() == 'quit':
                break
            if yoda_mode:
                line = yoda.yoda_speak(line)
            out = translator.translate_sentence(line)
            print(out)
            if f:
                f.write(out + "\n")
                f.flush()
    finally:
        if f:
            f.close()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['a', 'auto', 'i', 'interactive'])
    parser.add_argument('--lexicon', default=os.path.join(base_dir, 'conlang_lexicon.json'))
    parser.add_argument('--convo', default=None)
    parser.add_argument('--output', default=os.path.join(base_dir, 'translation'))
    parser.add_argument('--yoda', action='store_true')
    args = parser.parse_args()
    if not args.mode:
        parser.print_help()
        return


    _configure_utf8_stdout()

    try:
        translator = _load_translator(args.lexicon)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: {args.lexicon} not found.")
        print("Please run the Generator Script first to create the dictionary file.")
        return

    print(f"Dictionary loaded: {len(translator.lexicon)} words.")

    if args.mode == 'interactive' or args.mode == 'i':
        run_interactive(translator, output_path=args.output, yoda_mode=args.yoda)
        return

    convo_path = args.convo
    if convo_path is None:
        convo_path = _detect_convo_path(base_dir)
    if convo_path is None:
        raise FileNotFoundError("No such file or directory: convo.csv (also tried convo..csv)")

    if args.yoda:
        sentences = _read_convo_sentences(convo_path)
        with open(args.output, "w", encoding="utf-8") as f:
            last = ""
            print("-" * 50)
            for set in sentences:
                if last == set:
                    continue
                test = set.split('.')
                if len(test) > 1:
                    for myset in test:
                        if last == myset:
                            continue
                        out = translator.translate_sentence(yoda.yoda_speak(set))
                    continue
                out = translator.translate_sentence(yoda.yoda_speak(set))
                if out == last:
                    continue
                print(out)
                f.write(out + "\n")
                f.flush()
                last = out
                #time.sleep(1)
        return

    run_auto(translator, convo_path, args.output)


if __name__ == '__main__':
    main()

