import warnings
# Filter specific spaCy warnings about empty vectors
warnings.filterwarnings("ignore", category=UserWarning, message=".*Evaluating Doc.similarity based on empty vectors.*")

import json
import math
import spacy
import en_core_web_lg
from nltk.corpus import wordnet as wn

# Load the large English model
nlp = en_core_web_lg.load(disable=["tagger", "parser", "ner", "lemmatizer", "attribute_ruler"])

results = {}

# ---------------------------------------------------------
# 1. WU XING (FIVE ELEMENTS) ANCHOR DEFINITIONS
# ---------------------------------------------------------

anchors = {
    'wood': [
        'Wood', 'Tree', 'Forest', 'Plants', 'Bamboo',
        'Spring', 'Wind', 'East', 'Green',
        'Growth', 'Expansion', 'Sprouting', 'Vision', 'Creativity',
        'Liver', 'Gallbladder', 'Anger', 'Kindness', 'Altruism',
        'Flexible', 'Rooted', 'Upward'
    ],
    'fire': [
        'Fire', 'Flame', 'Sun', 'Heat', 'Light',
        'Summer', 'South', 'Red', 'Scorched',
        'Ascension', 'Dynamic', 'Transformation', 'Combustion',
        'Heart', 'Small Intestine', 'Tongue', 'Joy', 'Passion',
        'Spirit', 'Consciousness', 'Propriety', 'Laughter'
    ],
    'earth': [
        'Earth', 'Soil', 'Ground', 'Mountain', 'Clay', 'Sand',
        'Late Summer', 'Center', 'Yellow', 'Sweet',
        'Stability', 'Balance', 'Transformation', 'Harvest', 'Nourishment',
        'Spleen', 'Stomach', 'Mouth', 'Flesh',
        'Worry', 'Empathy', 'Pensiveness', 'Trust', 'Grounding'
    ],
    'metal': [
        'Metal', 'Gold', 'Silver', 'Iron', 'Mineral', 'Rock', 'Ore',
        'Autumn', 'West', 'White', 'Dryness',
        'Contraction', 'Structure', 'Refinement', 'Separation', 'Cutting',
        'Lungs', 'Large Intestine', 'Nose', 'Skin',
        'Grief', 'Sadness', 'Righteousness', 'Bravery', 'Organization'
    ],
    'water': [
        'Water', 'Ocean', 'River', 'Rain', 'Ice', 'Cold',
        'Winter', 'North', 'Black', 'Blue', 'Salty',
        'Flow', 'Descending', 'Storage', 'Rest', 'Hibernation',
        'Kidneys', 'Bladder', 'Ears', 'Bone',
        'Fear', 'Willpower', 'Wisdom', 'Adaptability', 'Fluidity'
    ]
}

# Pre-compute vector docs for anchors to speed up processing
print("Pre-computing anchor vectors...")
ANCHOR_DOCS = {k: list(nlp.pipe(v, batch_size=64)) for k, v in anchors.items()}
print("Vectors loaded.")

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------

def log_scale(value, in_min=0.2, in_max=0.8, out_max=63):
    """Map similarity value from [in_min, in_max] to [0, out_max] using log scale"""
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
    synsets = wn.synsets(word)
    if not synsets:
        return None

    # Iterate through all synsets for the word
    for syn in synsets:
        name = syn.name()
        
        # Filter logic from original script
        if len(name.split("_")) > 2:
            continue
            
        nameparts = name.split('.')
        if len(nameparts) > 3:
            continue

        defn = syn.definition()
        
        # Heuristic: Weight the vector towards the word itself (3x) + definition
        sword = word * 3
        doc = nlp(f"{sword} {defn}")

        # Initialize the Five Elements
        composition = {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0}
        
        closest_spirit = ""
        global_max_sim = 0

        # Compare against all anchors
        for key in anchors:
            local_max_sim = 0
            for anchor_doc in ANCHOR_DOCS[key]:
                sim = doc.similarity(anchor_doc)
                if sim > local_max_sim:
                    local_max_sim = sim
            
            # Update composition score for this element
            score = log_scale(local_max_sim)
            if composition[key] < score:
                composition[key] = score
            
            # Track the dominant element across all keys
            if local_max_sim > global_max_sim:
                global_max_sim = local_max_sim
                closest_spirit = key

        # Construct result object
        data = {
            'spirit': closest_spirit, 
            'composition': composition, 
            'definition': defn
        }
        
        results[name] = data
        total = len(results.keys())
        print(f"Processed {total} | {name:<30}", end="\r")

    return True

# ---------------------------------------------------------
# 3. MAIN EXECUTION
# ---------------------------------------------------------

def main():
    # Read words from file
    try:
        with open('words.txt', 'r') as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: words.txt not found in the current directory.")
        return
    
    # Process each word
    total_words = len(words)
    print(f"Processing {total_words} words against Wu Xing (5 Elements)...")
    
    for i, word in enumerate(words, 1):
        process_word(word)

    print("\n" + "*"*50)
    print("Processing Complete.")
    
    # Save to JSON
    output_filename = 'five_elements_dict.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(results.keys())} entries to {output_filename}")

if __name__ == "__main__":
    main()