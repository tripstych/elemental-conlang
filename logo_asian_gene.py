import warnings
warnings.filterwarnings("ignore")

import json
import operator
import random
import spacy
import en_core_web_lg
from nltk.corpus import wordnet as wn

# Load Model
print("Loading Model...")
nlp = en_core_web_lg.load(disable=["parser", "ner", "lemmatizer", "attribute_ruler"])

# --- 1. CONFIGURATION ---

ONSET_PHONES = {
    'n': ['b', 'd', 'g', 'm', 'n', 'l', 'zh', 'dr', 'bl'], 
    'v': ['p', 't', 'k', 'ch', 'q', 'r', 'tr', 'kr'],      
    'a': ['f', 's', 'x', 'sh', 'h', 'sw'],                  
    'r': ['l', 'r', 'w', 'y', 'ly'],                        
    's': ['z', 'ts', 'c', 's', 'dz'],                       
    'e': ['h', 'x', 'y', 'w', ''],                          
    'k': ['g', 'k', 'ng', 'gw'],                            
    'i': ['j', 'q', 'x', 'y'],                              
    'd': ['zh', 'ch', 'd', 'z', 'th'],                      
    'o': ['b', 'p', 'm', 'f']                               
}

NUCLEUS_VOWELS = {
    'wood':  ['i', 'e', 'ia', 'ie', 'ae'],
    'fire':  ['a', 'ai', 'ao', 'au', 'ia'],
    'earth': ['u', 'o', 'ou', 'uo', 'uh'],
    'metal': ['ei', 'oi', 'iu', 'ue', 'ee'],
    'water': ['yu', 'ui', 'yo', 'wa', 'oe']
}

TONES = {
    'wood':  1, 'fire':  2, 'earth': 3, 'metal': 4, 'water': 5
}

SUFFIX_SYLLABLES = {
    'wood':  ['la', 'ki', 'ne'],
    'fire':  ['ra', 'ti', 'na'],
    'earth': ['mu', 'ngu', 'ba'],
    'metal': ['si', 'k', 't'],
    'water': ['wa', 'yo', 'm']
}

ANCHORS = {
    'wood': ['Wood', 'Tree', 'Growth', 'Spring', 'East'],
    'fire': ['Fire', 'Sun', 'Heat', 'Summer', 'South'],
    'earth': ['Earth', 'Mountain', 'Center', 'Yellow', 'Stability'],
    'metal': ['Metal', 'Gold', 'Autumn', 'West', 'White'],
    'water': ['Water', 'Ocean', 'Winter', 'North', 'Black']
}

print("Pre-computing anchors...")
ANCHOR_DOCS = {k: list(nlp.pipe(v, batch_size=64)) for k, v in ANCHORS.items()}


# --- 2. LOGIC ---

def map_pos_to_key(pos_tag, source='spacy'):
    spacy_map = {
        'NOUN': 'n', 'PROPN': 'n', 'VERB': 'v', 'AUX': 'v', 'ADJ': 'a',
        'ADV': 'r', 'INTJ': 'e', 'CCONJ': 'k', 'SCONJ': 'k', 'ADP': 'i',
        'PRON': 'd', 'DET': 'd', 'NUM': 'o', 'SYM': 'o', 'X': 'o'
    }
    if source == 'wordnet':
        return pos_tag if pos_tag in ONSET_PHONES else 'n'
    return spacy_map.get(pos_tag, 'n')

def get_composition(doc):
    comp = {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0}
    max_score = 0
    spirit = 'water'
    
    for key in ANCHORS:
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

def generate_raw_syllable(phon_key, primary, secondary):
    onset = random.choice(ONSET_PHONES.get(phon_key, ONSET_PHONES['n']))
    vowel = random.choice(NUCLEUS_VOWELS.get(primary, NUCLEUS_VOWELS['water']))
    
    if secondary == 'metal' or random.random() > 0.7:
        coda = random.choice(['n', 'ng', 'm', 'k'])
        return f"{onset}{vowel}{coda}"
    
    return f"{onset}{vowel}"

def make_unique(base_word, tone, composition, reverse_lookup, phon_key):
    # 1. Simple Tone
    candidate = f"{base_word}{tone}"
    if candidate not in reverse_lookup:
        return candidate

    # 2. Alternate Vowels
    primary = max(composition, key=composition.get)
    for _ in range(5):
        # Pick a random secondary influence for variety
        sec = random.choice(list(composition.keys()))
        alt_base = generate_raw_syllable(phon_key, primary, sec)
        cand = f"{alt_base}{tone}"
        if cand not in reverse_lookup:
            return cand

    # 3. Polysyllabic (SAFE VERSION)
    sorted_items = sorted(composition.items(), key=lambda x: x[1], reverse=True)
    
    # FIX: Safety check for index out of range
    if len(sorted_items) > 1:
        secondary = sorted_items[1][0]
    else:
        secondary = sorted_items[0][0] # Fallback to primary if only 1 exists

    suffixes = SUFFIX_SYLLABLES.get(secondary, ['la'])
    
    for suf in suffixes:
        cand = f"{base_word}{suf}" 
        if cand not in reverse_lookup:
            return cand
        cand = f"{base_word}{suf}{tone}"
        if cand not in reverse_lookup:
            return cand

    return f"{base_word}zi{random.randint(1,9)}"

# --- 3. MAIN ---

def main():
    try:
        with open('words.txt', 'r') as f:
            words = list(dict.fromkeys([w.strip() for w in f if w.strip()]))
    except:
        print("words.txt not found")
        return

    print(f"Processing {len(words)} words...")
    
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
                'pos': syn.name().split('.')[1]
            })

    print("Vectorizing...")
    texts = [e['text'] for e in entries]
    docs = list(nlp.pipe(texts, batch_size=200))

    results = {}
    reverse_lookup = set()
    
    print("Generating...")
    for entry, doc in zip(entries, docs):
        
        if not doc.has_vector or doc.vector_norm == 0:
            # FIX: Initialize full dictionary to prevent index error
            spirit = 'water'
            comp = {'wood': 10, 'fire': 10, 'earth': 10, 'metal': 10, 'water': 60}
        else:
            spirit, comp = get_composition(doc)

        sorted_el = sorted(comp.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_el[0][0]
        secondary = sorted_el[1][0] if len(sorted_el) > 1 else primary
        
        tone = TONES[secondary]

        if entry['type'] == 'fb':
            spacy_pos = doc[0].pos_ if len(doc)>0 else 'X'
            phon_key = map_pos_to_key(spacy_pos, 'spacy')
        else:
            phon_key = map_pos_to_key(entry['pos'], 'wordnet')

        base = generate_raw_syllable(phon_key, primary, secondary)
        final_word = make_unique(base, tone, comp, reverse_lookup, phon_key)
        
        reverse_lookup.add(final_word)
        results[entry['word']] = {
            'word': final_word,
            'spirit': spirit,
            'tone': tone
        }

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='asian_lexicon.json')
    args = parser.parse_args()
    out = args.output
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} to {out} words.")

if __name__ == "__main__":
    main()