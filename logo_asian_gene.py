import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import json
import math
import operator
import random
import spacy
import en_core_web_lg
from nltk.corpus import wordnet as wn

# Load spaCy
print("Loading Language Model...")
nlp = en_core_web_lg.load(disable=["parser", "ner", "lemmatizer", "attribute_ruler"])
print("Model Loaded.")

# ---------------------------------------------------------
# 1. WU XING ANCHORS
# ---------------------------------------------------------

anchors = {
    'wood': ['Wood', 'Tree', 'Growth', 'Spring', 'East', 'Green', 'Creativity', 'Liver', 'Start'],
    'fire': ['Fire', 'Sun', 'Heat', 'Summer', 'South', 'Red', 'Passion', 'Heart', 'Action'],
    'earth': ['Earth', 'Mountain', 'Center', 'Yellow', 'Stability', 'Stomach', 'Sweet', 'Solid'],
    'metal': ['Metal', 'Gold', 'Autumn', 'West', 'White', 'Lungs', 'Grief', 'Structure', 'Cut'],
    'water': ['Water', 'Ocean', 'Winter', 'North', 'Black', 'Kidney', 'Fear', 'Flow', 'Wisdom', 'Mystery']
}

print("Pre-computing anchor vectors...")
ANCHOR_DOCS = {k: list(nlp.pipe(v, batch_size=64)) for k, v in anchors.items()}

# ---------------------------------------------------------
# 2. PHONOLOGY CONFIG (FULL 10-KEY SYSTEM)
# ---------------------------------------------------------

# EXPANDED ONSETS: Unique sound signatures for every POS type
ONSET_PHONES = {
    # Nouns: Stable, unaspirated stops & nasals
    'n': ['b', 'd', 'g', 'm', 'n', 'l'],
    
    # Verbs: Active, aspirated stops & affricates
    'v': ['p', 't', 'k', 'ch', 'q', 'r'],
    
    # Adjectives: Descriptive, fricatives
    'a': ['f', 's', 'x', 'sh'],
    
    # Adverbs: Flowing, liquids
    'r': ['l', 'r', 'w', 'y'],

    # Adjective Satellites (s): Sharp, sibilant precision
    's': ['z', 'ts', 'c', 's'],

    # Exclamations/Interjections (e): Breathy, open
    'e': ['h', 'x', 'y', 'w', ''],

    # Conjunctions (k): Connectors, velar/guttural
    'k': ['g', 'k', 'ng', 'h'],

    # Prepositions (i): Relational, dental/palatal
    'i': ['j', 'q', 'x', 'y'],

    # Determiners/Pronouns (d): Deictic (pointing), dentals/retroflex
    'd': ['zh', 'ch', 'd', 'z', 'n'],

    # Others/Numbers (o): Labials (easy to count)
    'o': ['b', 'p', 'm', 'f']
}

# Vowels determined by Element
NUCLEUS_VOWELS = {
    'wood':  ['i', 'e', 'ia', 'ie', 'ye'],
    'fire':  ['a', 'ai', 'ao', 'ya', 'ua'],
    'earth': ['u', 'o', 'ou', 'uo', 'e'],
    'metal': ['ei', 'ui', 'iu', 'ue'],
    'water': ['yu', 'oi', 'yo', 'wa']
}

# Codas determined by Secondary Element
CODAS = {
    'wood':  ['n', 'l'],
    'fire':  ['ng', 'n'],
    'earth': ['m', 'ng'],
    'metal': ['k', 't'],
    'water': ['m', 'n', 'ng']
}

# ---------------------------------------------------------
# 3. ROBUST POS MAPPING
# ---------------------------------------------------------

def map_pos_to_key(pos_tag, source='spacy'):
    """Maps varied tags to our strict 10-key phonology system."""
    
    # 1. WORDNET MAPPING
    if source == 'wordnet':
        # WordNet tags: n, v, a, r, s
        return pos_tag if pos_tag in ONSET_PHONES else 'n'

    # 2. SPACY MAPPING
    # Maps Universal POS tags to our custom keys
    spacy_map = {
        'NOUN': 'n', 'PROPN': 'n',
        'VERB': 'v', 'AUX': 'v',
        'ADJ': 'a',
        'ADV': 'r',
        'INTJ': 'e',
        'CCONJ': 'k', 'SCONJ': 'k',  # Connectors
        'ADP': 'i',                  # Prepositions (In/On/At)
        'PRON': 'd', 'DET': 'd',     # Determiners/Pronouns (The/This/I)
        'NUM': 'o', 'SYM': 'o', 'X': 'o'
    }
    return spacy_map.get(pos_tag, 'n') # Default to Noun

# ---------------------------------------------------------
# 4. GENERATION LOGIC
# ---------------------------------------------------------

def log_scale(value, in_min=0.2, in_max=0.8, out_max=63):
    if in_min <= 0 or in_max <= 0 or in_min >= in_max: return 0
    if value <= in_min: return 0
    if value >= in_max: return out_max
    log_min = math.log(in_min)
    log_max = math.log(in_max)
    scale = (math.log(value) - log_min) / (log_max - log_min)
    return max(0, min(out_max, int(round(scale * out_max))))

def calculate_composition(doc_text):
    doc = nlp(doc_text)
    composition = {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0}
    closest_spirit = ""
    global_max_sim = 0

    for key in anchors:
        local_max_sim = 0
        for anchor_doc in ANCHOR_DOCS[key]:
            sim = doc.similarity(anchor_doc)
            if sim > local_max_sim:
                local_max_sim = sim
        
        score = log_scale(local_max_sim)
        composition[key] = score
        
        if local_max_sim > global_max_sim:
            global_max_sim = local_max_sim
            closest_spirit = key
            
    return closest_spirit, composition

def construct_word(phon_key, vector, reverse_lookup):
    """
    phon_key: One of ['n', 'v', 'a', 'r', 's', 'e', 'k', 'i', 'd', 'o']
    """
    sorted_elements = sorted(vector.items(), key=operator.itemgetter(1), reverse=True)
    primary = sorted_elements[0][0]
    secondary = sorted_elements[1][0] if len(sorted_elements) > 1 else primary
    
    # 1. Get Onset based on strict POS key
    onset_options = ONSET_PHONES.get(phon_key, ONSET_PHONES['n'])
    onset = random.choice(onset_options)
    
    # 2. Get Nucleus based on Primary Element
    nucleus = random.choice(NUCLEUS_VOWELS.get(primary, NUCLEUS_VOWELS['water']))
    
    # 3. Structure Logic
    roll = random.random()
    if roll < 0.5: # CV (Open)
        word = f"{onset}{nucleus}"
    elif roll < 0.9: # CVC (Closed)
        coda = random.choice(CODAS.get(secondary, ['n']))
        word = f"{onset}{nucleus}{coda}"
    else: # CVV (Complex)
        nucleus2 = random.choice(NUCLEUS_VOWELS.get(secondary, NUCLEUS_VOWELS['water']))
        word = f"{onset}{nucleus}{nucleus2}"
        
    return word

def resolve_homonym(word, reverse_lookup, attempts=50):
    for _ in range(attempts):
        suffix = random.choice(['n', 'a', 'o', 'i'])
        candidate = word + suffix
        if candidate not in reverse_lookup:
            return candidate
    return word + str(random.randint(1,9))

# ---------------------------------------------------------
# 5. PROCESSORS
# ---------------------------------------------------------

results = {}
reverse_lookup = set()

def process_fallback(word):
    """Handles pronouns, prepositions, conjunctions (Not in WordNet)."""
    doc = nlp(word)
    
    # Bias logic for function words
    if not doc.has_vector or doc.vector_norm == 0:
        composition = {'wood': 20, 'fire': 20, 'earth': 20, 'metal': 20, 'water': 60}
        spirit = 'water'
        spacy_tag = 'X'
    else:
        spirit, composition = calculate_composition(word)
        spacy_tag = doc[0].pos_
        
        # Heavy bias for function words to make them feel fundamental
        if spacy_tag in ['PRON', 'DET']: # 'd' key
            composition['earth'] = max(composition['earth'], 50) # Deixis is grounding
        elif spacy_tag in ['ADP', 'CCONJ']: # 'i', 'k' keys
            composition['metal'] = max(composition['metal'], 50) # Connectors are structural

    # Map spaCy tag to our 10-key system
    phon_key = map_pos_to_key(spacy_tag, source='spacy')
    
    gen_word = construct_word(phon_key, composition, reverse_lookup)
    while gen_word in reverse_lookup:
        gen_word = resolve_homonym(gen_word, reverse_lookup)
        
    reverse_lookup.add(gen_word)
    
    # Save with a clean key
    key = f"{word}.{phon_key}.00"
    results[key] = {
        'spirit': spirit,
        'composition': composition,
        'definition': f"[{spacy_tag}] {word}",
        'word': gen_word
    }
    print(f"Fallback: {word:<15} -> {gen_word:<10} (Key: {phon_key})")

def process_word(word):
    synsets = wn.synsets(word)
    
    if not synsets:
        process_fallback(word)
        return

    processed_any = False
    for syn in synsets:
        name = syn.name()
        if len(name.split("_")) > 2: continue
        
        wn_pos = name.split('.')[1] # n, v, a, r, s
        defn = syn.definition()
        
        # Calculate Vectors
        text_for_vec = f"{word} {word} {defn}"
        spirit, composition = calculate_composition(text_for_vec)
        
        # Map WordNet POS to our 10-key system
        # Note: WordNet uses 's' for satellite adjectives, which we support now!
        phon_key = map_pos_to_key(wn_pos, source='wordnet')
        
        gen_word = construct_word(phon_key, composition, reverse_lookup)
        
        # Homonym resolution
        retry = 0
        while gen_word in reverse_lookup and retry < 20:
             gen_word = construct_word(phon_key, composition, reverse_lookup)
             retry += 1
        if gen_word in reverse_lookup:
             gen_word = resolve_homonym(gen_word, reverse_lookup)
             
        reverse_lookup.add(gen_word)
        
        results[name] = {
            'spirit': spirit,
            'composition': composition,
            'definition': defn,
            'word': gen_word
        }
        processed_any = True
        
    if not processed_any:
        process_fallback(word)
    else:
        # Just print the first one as a sample
        print(f"Processed: {word:<15}")

def main():
    try:
        with open('words.txt', 'r') as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: words.txt not found.")
        return

    print(f"Processing {len(words)} words...")
    
    for word in words:
        process_word(word)

    output_file = 'final_asian_lexicon_10key.json'
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    main()