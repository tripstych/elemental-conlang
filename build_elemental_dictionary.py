import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*Evaluating Doc.similarity based on empty vectors.*")

import math
import json
import random
import numpy as np
import argparse
from tqdm import tqdm
import spacy
from collections import Counter
from itertools import combinations
from wordfreq import zipf_frequency, top_n_list
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from pattern.text.en import singularizer

import en_core_web_lg
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

# Parse command line arguments for custom anchors file
parser = argparse.ArgumentParser(description='Build elemental dictionary with optional custom anchors')
parser.add_argument('--anchor', type=str, help='JSON file containing custom anchors dictionary')
parser.add_argument('--output', default="elemental_source.json", help="Output file name")
args, unknown = parser.parse_known_args()

# Load custom anchors if provided, otherwise use default
if args.anchor:
    try:
        with open(args.anchor, 'r', encoding='utf-8') as f:
            custom_anchors = json.load(f)
        # Validate that it's a proper anchors dictionary
        if isinstance(custom_anchors, dict) and all(isinstance(v, list) for v in custom_anchors.values()):
            anchors = custom_anchors
            print(f"Loaded custom anchors from {args.anchor}")
        else:
            print(f"Invalid anchors format in {args.anchor}, using default anchors")
    except FileNotFoundError:
        print(f"Anchor file {args.anchor} not found, using default anchors")
    except json.JSONDecodeError as e:
        print(f"Error parsing anchors file {args.anchor}: {e}, using default anchors")
else:
    print("Using default anchors")

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

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        print(len(results.keys()))
    
    
    
if __name__ == "__main__":
    main()
