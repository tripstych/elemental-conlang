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
        with open('words.txt', 'r') as f:
            words = list(dict.fromkeys([w.strip() for w in f if w.strip()]))
    except:
        print("words.txt not found")
        return

    print(f"Processing {len(words)} words...")
    allocator = WordAllocator()
    entries = []

    for w in words:
        synsets = wn.synsets(w)
        if not synsets:
            entries.append({'type': 'fb', 'word': w, 'text': w})
        else:
            syn = synsets[0]
            entries.append({
                'type': 'wn', 
                'word': w, 
                'text': f"{w} {syn.definition()}",
                'pos': syn.name().split('.')[1],
                'definition': syn.definition(),
                'key': syn.name() # Use the specific WordNet key (e.g. on.r.02)
            })

    print("Vectorizing...")
    texts = [e['text'] for e in entries]
    docs = list(nlp.pipe(texts, batch_size=256))
    results = {}
    
    print("Generating & Allocating...")
    for i, (entry, doc) in enumerate(zip(entries, docs)):
        
        if not doc.has_vector or doc.vector_norm == 0:
            spirit, comp = 'water', {'wood': 20, 'fire': 20, 'earth': 20, 'metal': 20, 'water': 60}
        else:
            spirit, comp = get_composition(doc)

        sorted_el = sorted(comp.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_el[0][0]
        secondary = sorted_el[1][0] if len(sorted_el) > 1 else primary
        
        if entry['type'] == 'fb':
            spacy_pos = doc[0].pos_ if len(doc)>0 else 'X'
            phon_key = map_pos_to_key(spacy_pos, 'spacy')
            entry_key = f"{entry['word']}.{phon_key}.00" # Fallback key format
            definition = f"[{spacy_pos}] {entry['word']}"
        else:
            phon_key = map_pos_to_key(entry['pos'], 'wordnet')
            entry_key = entry['key']
            definition = entry['definition']

        final_word = allocator.get_word(primary, secondary, phon_key)
        
        # SAVE FULL FORMAT
        results[entry_key] = {
            'spirit': spirit,
            'composition': comp,
            'definition': definition,
            'word': final_word
        }
        
        if i % 2000 == 0:
            print(f"  Processed {i} words...", end="\r")

    print(f"\nCompleted {len(results)} words.")
    
    with open('lexicon_final_full.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("Saved to 'lexicon_final_full.json'.")

if __name__ == "__main__":
    main()