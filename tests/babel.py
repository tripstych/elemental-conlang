import time
import sys
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import json
import os
import re

# --- NLTK SETUP (Run once) ---
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
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
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        translation = []
        for word, tag in tagged:
            # Pass through punctuation
            if not word.isalnum():
                translation.append(word)
                continue

            wn_pos = self.get_wordnet_pos(tag)
            lemma = self.lemmatizer.lemmatize(word.lower(), pos=wn_pos)

            target_key = self.find_best_key(lemma, wn_pos)
            if target_key and target_key in self.lexicon:
                translation.append(self.entry_to_word(self.lexicon[target_key], f"[{word}]"))
            else:
                translation.append(f"[{word}]")

        return " ".join(translation)

    @classmethod
    def from_json(cls, filename):
        """Load a lexicon JSON file and return a translator."""
        with open(filename, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        return cls(lexicon)

# --- MAIN EXECUTION ---

# 1. LOAD DATA
base_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(base_dir, 'conlang_lexicon.json') # Make sure this matches your saved file
if not os.path.exists(filename):
    print(f"CRITICAL ERROR: {filename} not found.")
    print("Please run the Generator Script first to create the dictionary file.")
else:
    translator = ConlangTranslator.from_json(filename)
    print(f"Dictionary loaded: {len(translator.lexicon)} words.")

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    # 2. RUN TRANSLATOR
    # 2. READ CONVERSATION
    convo_path = None
    for candidate in ('convo.csv', 'convo..csv'):
        p = os.path.join(base_dir, candidate)
        if os.path.exists(p):
            convo_path = p
            break
    if convo_path is None:
        raise FileNotFoundError("No such file or directory: convo.csv (also tried convo..csv)")

    with open(convo_path, 'r', encoding='utf-8') as f:
        sentences = []
        for line in f:
            match = re.search(r"'((?:\\'|[^'])*)'", line)
            if not match:
                continue
            sentence = match.group(1).replace("\\'", "'").strip()
            if sentence:
                sentences.append(sentence)

    f = open(os.path.join(base_dir, "translation"), "w", encoding="utf-8")

    last = ""
    print("-" * 50)
    for set in sentences:
        if last == set:
            continue
        test = set.split('.')
        if len(test)>1:
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

    f.close()