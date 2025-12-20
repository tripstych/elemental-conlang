import warnings
warnings.filterwarnings("ignore")

import json
import itertools
import random
import re
import spacy
import en_core_web_lg
from nltk.corpus import wordnet as wn

print("Loading Model...")
nlp = en_core_web_lg.load(disable=["parser", "ner", "lemmatizer", "attribute_ruler"])

# ---------------------------------------------------------
# 1. ORTHOGRAPHY & TONE MAPPING
# ---------------------------------------------------------

TONE_MAP = {
    1: {'a': 'ā', 'e': 'ē', 'i': 'ī', 'o': 'ō', 'u': 'ū'}, 
    2: {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'}, 
    3: {'a': 'ǎ', 'e': 'ě', 'i': 'ǐ', 'o': 'ǒ', 'u': 'ǔ'}, 
    4: {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù'}, 
    5: {'a': 'a', 'e': 'e', 'i': 'i', 'o': 'o', 'u': 'u'}  
}

def apply_tone(syllable, tone_id):
    if tone_id == 5: return syllable
    for char in ['a', 'e']:
        if char in syllable: return syllable.replace(char, TONE_MAP[tone_id][char], 1)
    if 'ou' in syllable: return syllable.replace('o', TONE_MAP[tone_id]['o'], 1)
    for i in range(len(syllable) - 1, -1, -1):
        if syllable[i] in "aeiou":
            char = syllable[i]
            return syllable[:i] + TONE_MAP[tone_id][char] + syllable[i+1:]
    return syllable

# ---------------------------------------------------------
# 2. PHONOLOGY CONFIGURATION
# ---------------------------------------------------------

ONSETS = {
    'n': ['b', 'd', 'g', 'm', 'n', 'l', 'zh', 'dr', 'bl', 'gl', 'gw', 'z', 'dz', 'br'], 
    'v': ['p', 't', 'k', 'ch', 'q', 'r', 'tr', 'kr', 'kl', 'pl', 'kw', 'pr', 'ts'],      
    'a': ['f', 's', 'x', 'sh', 'h', 'sw', 'sl', 'fl', 'th', 'shr', 'hw'],                  
    'r': ['l', 'r', 'w', 'y', 'ly', 'ry', 'wr'],                        
    's': ['z', 'ts', 'c', 's', 'dz'],                       
    'e': ['h', 'x', 'y', 'w', ''],                          
    'k': ['g', 'k', 'ng', 'gw'],                            
    'i': ['j', 'q', 'x', 'y'],                              
    'd': ['zh', 'ch', 'd', 'z', 'th', 'dh'],                      
    'o': ['b', 'p', 'm', 'f']                               
}

MEDIALS = {
    'wood':  ['i', 'y', 'r'],
    'fire':  ['i', 'y', 'w'],
    'earth': ['u', 'w'],
    'metal': ['u', 'w', 'r'],
    'water': ['u', 'w', 'y']
}

VOWELS = {
    'wood':  ['i', 'e', 'ia', 'ie', 'ae', 'ea'],
    'fire':  ['a', 'ai', 'ao', 'au', 'ia', 'ua'],
    'earth': ['u', 'o', 'ou', 'uo', 'uh', 'oa'],
    'metal': ['ei', 'oi', 'iu', 'ue', 'ee', 'oe'],
    'water': ['yu', 'ui', 'yo', 'wa', 'oe', 'oi']
}

CODAS = {
    'wood':  ['n', 'l', 'r'],
    'fire':  ['ng', 'n', 'rn'],
    'earth': ['m', 'ng', 'mp'],
    'metal': ['k', 't', 'p', 'kt'], 
    'water': ['m', 'n', 'ng']
}

TONES = {'wood': 1, 'fire': 2, 'earth': 3, 'metal': 4, 'water': 5}

# ---------------------------------------------------------
# 3. THE GENERATOR
# ---------------------------------------------------------

class ElementalStream:
    def __init__(self, primary, secondary, phon_key):
        self.tone_id = TONES[secondary]
        self.onsets = ONSETS.get(phon_key, ONSETS['n'])
        self.vowels = VOWELS.get(primary, VOWELS['water'])
        self.codas = CODAS.get(secondary, ['n'])
        self.medials = MEDIALS.get(primary, [''])
        self.perm_gen = self._permutation_generator()

    def _permutation_generator(self):
        # TIER 1: Simple CV
        tier1 = list(itertools.product(self.onsets, self.vowels))
        random.shuffle(tier1)
        for o, v in tier1:
            yield apply_tone(f"{o}{v}", self.tone_id)

        # TIER 2: CVC
        tier2 = list(itertools.product(self.onsets, self.vowels, self.codas))
        random.shuffle(tier2)
        for o, v, c in tier2:
            yield apply_tone(f"{o}{v}{c}", self.tone_id)

        # TIER 3: CGVC
        tier3 = list(itertools.product(self.onsets, self.medials, self.vowels, self.codas))
        random.shuffle(tier3)
        valid_tier3 = []
        for o, m, v, c in tier3:
            if m and (o.endswith(m) or m in o): continue
            valid_tier3.append((o, m, v, c))
            yield apply_tone(f"{o}{m}{v}{c}", self.tone_id)

        # TIER 4: POLYSYLLABIC
        suffix_onsets = ONSETS['r'] + ONSETS['l'] if 'l' in ONSETS else ['l', 'n', 's']
        suffix_vowels = ['a', 'i', 'o']
        suffixes = list(itertools.product(suffix_onsets, suffix_vowels))
        random.shuffle(suffixes)
        random.shuffle(valid_tier3)
        
        for root in valid_tier3:
            o, m, v, c = root
            root_str = apply_tone(f"{o}{m}{v}{c}", self.tone_id)
            for so, sv in suffixes:
                yield f"{root_str}{so}{sv}"

    def next_candidate(self):
        return next(self.perm_gen)

class WordAllocator:
    def __init__(self):
        self.streams = {}
        self.global_registry = set() 

    def get_word(self, primary, secondary, phon_key):
        key = (primary, secondary, phon_key)
        if key not in self.streams:
            self.streams[key] = ElementalStream(primary, secondary, phon_key)
        
        stream = self.streams[key]
        while True:
            candidate = stream.next_candidate()
            if candidate not in self.global_registry:
                self.global_registry.add(candidate)
                return candidate

# ---------------------------------------------------------
# 4. MAIN EXECUTION
# ---------------------------------------------------------

anchors = {
    'wood': ['Wood', 'Growth', 'Spring', 'East'],
    'fire': ['Fire', 'Heat', 'Summer', 'South'],
    'earth': ['Earth', 'Center', 'Yellow', 'Stability'],
    'metal': ['Metal', 'Autumn', 'West', 'White'],
    'water': ['Water', 'Winter', 'North', 'Black']
}

print("Pre-computing anchors...")
ANCHOR_DOCS = {k: list(nlp.pipe(v, batch_size=64)) for k, v in anchors.items()}

def map_pos_to_key(pos_tag, source='spacy'):
    spacy_map = {
        'NOUN': 'n', 'PROPN': 'n', 'VERB': 'v', 'AUX': 'v', 'ADJ': 'a',
        'ADV': 'r', 'INTJ': 'e', 'CCONJ': 'k', 'SCONJ': 'k', 'ADP': 'i',
        'PRON': 'd', 'DET': 'd', 'NUM': 'o', 'SYM': 'o', 'X': 'o'
    }
    if source == 'wordnet':
        return pos_tag if pos_tag in ONSETS else 'n'
    return spacy_map.get(pos_tag, 'n')

def get_composition(doc):
    comp = {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0}
    max_score = 0
    spirit = 'water'
    for key in anchors:
        local_max = 0
        for anchor in ANCHOR_DOCS[key]:
            sim = doc.similarity(anchor)
            if sim > local_max: local_max = sim
        val = int(local_max * 100)
        comp[key] = val
        if val > max_score:
            max_score = val
            spirit = key
    return spirit, comp

def main():
    try:
        with open('elemental_dict.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"Loaded {len(results)} entries from 'elemental_dict.json'.")
        
        # Display some sample entries
        print("\nSample entries:")
        for i, (key, value) in enumerate(list(results.items())[:5]):
            print(f"  {key}: {value['word']} - {value['definition'][:50]}...")
        
        return results
        
    except FileNotFoundError:
        print("elemental_dict.json not found. Please ensure the generated JSON file exists.")
        return None
    except json.JSONDecodeError:
        print("Error parsing elemental_dict.json. Please check the file format.")
        return None

if __name__ == "__main__":
    main()