import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*Evaluating Doc.similarity based on empty vectors.*")

import json
import math

import en_core_web_lg
from nltk.corpus import wordnet as wn

nlp = en_core_web_lg.load(disable=["tagger", "parser", "ner", "lemmatizer", "attribute_ruler"])


results = {}
# 2. PHONETIC MAPPING (Base-4 Conlang)

anchors ={
    'air': [
        'Air', 'Verbs, Actions, Adverbs', 'Thought', 'Intellect', 
        'Communication', 'Respiration', 'Invisibility', 'Movement', 
        'Perspective', 'Agility', 'Atmosphere', 'Ascension', 
        'Vibration', 'Math', 'Formulas', 'Calculations'
    ],
    'water': [
        'Water', 'Emotion, Feeling, Adjectives, Pronouns', 'Fluidity', 'Emotion', 
        'Intuition', 'Reflection', 'Healing', 'Cohesion', 
        'Cycles', 'Submersion', 'Fertility', 'Passive Power', 
        'Lake', 'Ocean', 'River', 'Pond'
    ],
    'earth': [
        'Earth', 'Object / Nouns', 'Stability', 'Manifestation', 
        'Nourishment', 'Structure', 'Endurance', 'Fertility', 
        'Wealth', 'Sensation', 'Gravity', 'Decay', 
        'Ground', 'Earthwork', 'Clay', 'Land'
    ],
    'fire': [
        'Fire', 'Heat', 'Light', 'Flame', 
        'Lava', 'Magma', 'Conflict, Verbs, Interjections', 'Combustion', 
        'Incandescence', 'Transformation', 'Passion', 'Creativity', 
        'Purification', 'Vitality', 'Destruction', 'Willpower'
    ]
} 

ANCHOR_DOCS = {k: list(nlp.pipe(v, batch_size=64)) for k, v in anchors.items()}

def log_scale(value, in_min=0.2, in_max=0.8, out_max=63):
    """Map value from [in_min, in_max] to [0, out_max] using log scale"""
    if in_min <= 0 or in_max <= 0 or in_min >= in_max:
        return 0
    if value <= in_min:
        return 0
    if value >= in_max:
        return out_max

    log_min = math.log(in_min)
    log_max = math.log(in_max)
    denom = (log_max - log_min)
    if denom == 0:
        return 0
    scale = (math.log(value) - log_min) / denom
    scaled = int(round(scale * out_max))
    if scaled < 0:
        return 0
    if scaled > out_max:
        return out_max
    return scaled

def process_word(word):
    bump = 15 
    synsets = wn.synsets(word)
    if not synsets:
        return None

    # We don't need a global 'skipword' flag or 'final_composition'
    # We process and save each valid synonym individually.
    
    for syn in synsets:
        name = syn.name()
        if len(name.split("_"))>2:
            continue
        nameparts = name.split('.')
        
        # 1. Skip ONLY the specific bad synset, not the whole word
        if len(nameparts) > 3:
            continue

        type = name.split('.')[1]
        defn = syn.definition()
        sword = word*3
        doc = nlp(sword+" "+defn)

        composition = { 'earth' :0,'air':0, 'water':0,'fire':0}
        closest = ""
        max_sim = 0
        for key in anchors:
            for anchor_doc in ANCHOR_DOCS[key]:
                sim = doc.similarity(anchor_doc)
                if max_sim < sim:
                    closest = key
                    max_sim = sim
            if composition[key] < log_scale(max_sim):
                composition[key] = log_scale(max_sim)
        
        # Apply Bumps
        if False:
            if type == 'v':
                composition['air'] = max(64, composition['air'] + bump)
            if type == 'n':
                composition['earth'] = max(64, composition['earth'] + bump)
            if type == 'a':
                composition['water'] = max(64, composition['water'] + bump)
            if type == 'r':
                composition['fire'] = max(64, composition['fire'] + bump)

        # 2. Save IMMEDIATELY inside the loop
        data = { 'spirit': closest, 'composition': composition, 'definition': defn}
        results[name] = data
        total = len(results.keys())
        print(f"Processed {total} {name}                   ", end="\r")
        
        # Optional: Print progress per added synset if you want, 
        # or just keep the print in the main loop to reduce spam.
    
    return True

def _process_word(word):
    bump = 15 # bump for word types

    synsets = wn.synsets(word)
    if not synsets:
        return None

    final_composition = None
    skipword = False
    for syn in synsets:
        name = syn.name()
        nameparts = name.split('.')
        if len(nameparts)>3:
            skipword = True
            continue

        type = name.split('.')[1]
        defn = syn.definition()
        doc = nlp(defn)

        composition = {}
        for key in anchors:
            max_sim = -1.0
            for anchor_doc in ANCHOR_DOCS[key]:
                sim = doc.similarity(anchor_doc)
                if sim > max_sim:
                    max_sim = sim
            composition[key] = log_scale(max_sim)
        if type == 'v':
            composition['air'] = max(64, composition['air'] + bump)
        if type == 'n':
            composition['earth'] = max(64, composition['earth'] + bump)
        if type == 'a':
            composition['water'] = max(64, composition['water'] + bump)
        if type == 'r':
            composition['fire'] = max(64, composition['fire'] + bump)
        final_composition = composition

    if skipword:
        return
    data = { 'composition': final_composition, 'definition': defn}
    results[name] = data
    total = len(results.keys())
    print(f"Processed {total} {name}____________", end="\r")
    return data

def main():
    # Read words from file
    try:
        with open('words.txt', 'r') as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: words.txt not found in the current directory")
        return
    
    # Process each word
    total_words = len(words)
    print(f"Processing {total_words} words...")
    for i, word in enumerate(words, 1):
        process_word(word)

    print("*"*50)
    print("")
    with open('elemental_dict.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        print(len(results.keys()))
    
    
    
if __name__ == "__main__":
    main()
