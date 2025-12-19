import random
import operator
import json
import math
import os
import re
import itertools

# --- 1. SINO-XENIC PHONOLOGICAL CONFIGURATION ---

# Onsets: Categorized by Part of Speech (POS)
# Nouns = Solid, Unaspirated (Stability)
# Verbs = Aspirated, Affricates (Action/Change)
# Adjectives = Fricatives, Glides (Description/Flow)

ONSET_PHONES = {
    'n': ['b', 'd', 'g', 'm', 'n', 'l', 'z', 'zh', 'w'], 
    'v': ['p', 't', 'k', 'ch', 'c', 'j', 'q', 'r'],      
    'a': ['f', 's', 'x', 'h', 'sh', 'y', 'w'],           
    'r': ['l', 'r', 'w', 'y']                            
}

# Nucleus: The Vowel sound, determined by the DOMINANT Element
# Wood: Expansion (Front/High vowels)
# Fire: Brightness (Open/Low vowels)
# Earth: Center/Ground (Mid/Back vowels)
# Metal: Constriction (Tight/Diphthongs)
# Water: Depth (Rounded vowels)

NUCLEUS_VOWELS = {
    'wood':  ['i', 'e', 'ia', 'ie', 'ye'],
    'fire':  ['a', 'ai', 'ao', 'ya', 'ua'],
    'earth': ['u', 'o', 'ou', 'uo', 'e'], 
    'metal': ['ei', 'ui', 'iu', 'ue'],
    'water': ['yu', 'oi', 'yo', 'wa']
}

# Coda: The ending sound, determined by the SECONDARY Element
# Modeled after tonal languages (Nasals) and entering tones (Stops - p/t/k)

CODAS = {
    'wood':  ['n', 'l'],         # Gentle endings
    'fire':  ['ng', 'n'],        # Resonant, rising
    'earth': ['m', 'ng'],        # Heavy, grounding
    'metal': ['k', 't'],         # Sharp stops (Cantonese/Hakka style)
    'water': ['m', 'n', 'ng']    # Flowing nasals
}

# Particles used to glue compounds together (instead of apostrophes)
PARTICLES = ['no', 'zhi', 'de', 'ga', 'wa']

# --- 2. CORE GENERATOR FUNCTIONS ---

def mutate_vector(vector):
    """Adds slight random variance to the elemental composition."""
    elements = ['wood', 'fire', 'earth', 'metal', 'water']
    new_vec = vector.copy()
    for element in elements:
        val = new_vec.get(element, 0)
        new_vec[element] = min(0, max(64, val + random.randint(-10, 10)))
    return new_vec

def construct_word(pos, vector, reverse_lookup):
    """Builds a single syllable/word based on Wu Xing composition."""
    
    # Sort elements by intensity
    sorted_elements = sorted(vector.items(), key=operator.itemgetter(1), reverse=True)
    
    # Primary Element determines the Vowel (Soul of the word)
    primary = sorted_elements[0][0]
    
    # Secondary Element determines the Ending (Coda)
    if len(sorted_elements) > 1 and sorted_elements[1][1] > 0:
        secondary = sorted_elements[1][0]
    else:
        secondary = primary

    # POS determines the Start (Onset)
    # Fallback to 'n' if pos is unknown
    pos_key = pos if pos in ONSET_PHONES else 'n'
    
    onset = random.choice(ONSET_PHONES[pos_key])
    nucleus = random.choice(NUCLEUS_VOWELS.get(primary, NUCLEUS_VOWELS['earth']))
    
    # Determine syllable structure based on randomness and complexity
    structure_roll = random.random()
    
    # 40% Chance: Open Syllable (CV) - Japanese/Polynesian style
    if structure_roll < 0.4:
        word = f"{onset}{nucleus}"
        
    # 40% Chance: Closed Syllable (CVC) - Mandarin/Cantonese style
    elif structure_roll < 0.8:
        coda = random.choice(CODAS.get(secondary, ['n']))
        word = f"{onset}{nucleus}{coda}"
        
    # 20% Chance: Double Vowel/Complex (CVV)
    else:
        nucleus2 = random.choice(NUCLEUS_VOWELS.get(secondary, NUCLEUS_VOWELS['earth']))
        word = f"{onset}{nucleus}{nucleus2}"

    return word

def find_constituents(word, stem_lookup):
    """Scans for a valid split (fire + fly) where both parts exist."""
    min_len = 3 
    if len(word) < min_len * 2:
        return None
        
    for i in range(min_len, len(word) - min_len + 1):
        left, right = word[:i], word[i:]
        if left in stem_lookup and right in stem_lookup:
            return stem_lookup[left][0], stem_lookup[right][0]
    return None

def vectors_match(vec1, vec2, threshold=15.0):
    """Returns True if vectors are semantically close."""
    dist = 0
    # Updated for 5 Elements
    for k in ['wood', 'fire', 'earth', 'metal', 'water']:
        v1 = vec1.get(k, 0)
        v2 = vec2.get(k, 0)
        dist += (v1 - v2) ** 2
    return math.sqrt(dist) < threshold

def composition_signature(composition):
    return (
        composition.get('wood', 0),
        composition.get('fire', 0),
        composition.get('earth', 0),
        composition.get('metal', 0),
        composition.get('water', 0),
    )

# --- 3. COMPOUND LOGIC ---

def get_best_match(word_part, stem_index):
    if word_part not in stem_index:
        return None
    options = stem_index[word_part]
    # Priority: Noun > Verb > First available
    for opt in options:
        if '.n.' in opt: return opt
    for opt in options:
        if '.v.' in opt: return opt
    return options[0]

def assemble_compound(stem, stem_index, elemental_dict):
    parts = []
    
    # CASE A: Explicit Compound (underscores)
    if '_' in stem:
        raw_parts = stem.split('_')
        for p in raw_parts:
            match = get_best_match(p, stem_index)
            if match:
                parts.append(match)
    
    # CASE B: Implicit Compound (glued)
    elif not parts: 
        constituents = find_constituents(stem, stem_index)
        if constituents:
            parts = list(constituents) 

    if len(parts) >= 2:
        return parts

    return None

# --- 4. HOMONYM RESOLUTION & UTILS ---

def _build_phoneme_units():
    units = set()
    for cat in ONSET_PHONES.values(): units.update(cat)
    for cat in NUCLEUS_VOWELS.values(): units.update(cat)
    for cat in CODAS.values(): units.update(cat)
    return units

def tokenize_phonemes(word):
    # Simple tokenizer used for scrambling logic
    # In this Asian-style conlang, we can treat vowels/diphthongs as units
    phoneme_units = _build_phoneme_units()
    digraphs = sorted([u for u in phoneme_units if len(u) > 1], key=len, reverse=True)
    
    tokens = []
    i = 0
    while i < len(word):
        match_found = False
        for dg in digraphs:
            if word.startswith(dg, i):
                tokens.append(dg)
                i += len(dg)
                match_found = True
                break
        if not match_found:
            tokens.append(word[i])
            i += 1
    return tokens

def resolve_homonym(word, reverse_lookup, attempts=50):
    """
    Tries to modify a word slightly to fix collisions.
    Strategy: Swap the vowel (nucleus) or the coda while keeping the onset.
    """
    tokens = tokenize_phonemes(word)
    if not tokens: return None
    
    # Basic logic: Try to change the last token (often vowel or coda)
    # or the middle token.
    
    for _ in range(attempts):
        if len(tokens) == 1:
            # Single unit? append a particle
            candidate = word + random.choice(['n', 'a', 'o'])
        else:
            new_tokens = tokens[:]
            # Pick a random position to mutate (avoiding onset if possible)
            idx = random.randint(max(0, len(tokens)-2), len(tokens)-1)
            
            # Replace with random vowel or coda
            all_options = []
            for k in NUCLEUS_VOWELS: all_options.extend(NUCLEUS_VOWELS[k])
            for k in CODAS: all_options.extend(CODAS[k])
            
            new_tokens[idx] = random.choice(all_options)
            candidate = "".join(new_tokens)
            
        if candidate not in reverse_lookup:
            return candidate
            
    return None

def resolve_remaining_homonyms(final_lexicon, reverse_lookup):
    # Iterate through lexicon to find duplicates and fix them
    word_map = {}
    for k, v in final_lexicon.items():
        w = v['word']
        word_map.setdefault(w, []).append(k)
        
    for w, keys in word_map.items():
        if len(keys) > 1:
            # Collision detected
            # Keep the first one, mutate the rest
            for i in range(1, len(keys)):
                k = keys[i]
                new_word = resolve_homonym(w, reverse_lookup)
                if new_word:
                    final_lexicon[k]['word'] = new_word
                    reverse_lookup.add(new_word)
                    # print(f"Resolved collision for {k}: {w} -> {new_word}")

# --- 5. MAIN CLASS ---

class LexiconGenerator:
    def __init__(self, elemental_dict):
        self.elemental_dict = elemental_dict
        self.stem_index = {}
        for key in self.elemental_dict:
            stem = key.split('.')[0]
            self.stem_index.setdefault(stem, []).append(key)

        self.final_lexicon = {}
        self.reverse_lookup = set()
        self.word_compositions = {}
        self.stem_history = {} # Maps stem -> [(comp, word)]
        self.compound_keys = []

    def _register_word(self, stem, composition, word):
        self.reverse_lookup.add(word)
        self.word_compositions.setdefault(word, set()).add(composition_signature(composition))
        self.stem_history.setdefault(stem, []).append((composition, word))

    def _generate_base_word(self, stem, pos, composition):
        # 1. Check history for consistency
        if stem in self.stem_history:
            for prev_vector, prev_word in self.stem_history[stem]:
                if vectors_match(composition, prev_vector):
                    return prev_word

        # 2. Generate new
        max_retries = 20
        for _ in range(max_retries):
            candidate = construct_word(pos, composition, self.reverse_lookup)
            
            # Collision Check
            if candidate not in self.reverse_lookup:
                return candidate
            
            # Allow homonyms if compositions are identical (same word sense)
            sig = composition_signature(composition)
            if sig in self.word_compositions.get(candidate, set()):
                return candidate

        # 3. Last ditch resolve
        return resolve_homonym(candidate, self.reverse_lookup)

    def generate_base_lexicon(self):
        for key in self.elemental_dict:
            data = self.elemental_dict[key]
            stem = key.split('.')[0]

            if '_' in stem:
                self.compound_keys.append(key)
                continue

            pos = key.split('.')[1]
            composition = data.get('composition', {})

            unique_word = self._generate_base_word(stem, pos, composition)
            if unique_word is None:
                continue

            self._register_word(stem, composition, unique_word)

            entry = dict(data)
            entry['word'] = unique_word
            self.final_lexicon[key] = entry

    def generate_compounds(self):
        print(f"Processing {len(self.compound_keys)} compounds...")
        for key in self.compound_keys:
            stem = key.split('.')[0]
            composition = self.elemental_dict[key].get('composition', {})

            parts = assemble_compound(stem, self.stem_index, self.elemental_dict)
            if not parts:
                # If cannot build from parts, treat as base word
                unique_word = self._generate_base_word(stem, 'n', composition)
            else:
                # Build compound string
                part_words = []
                for p in parts:
                    if p in self.final_lexicon:
                        part_words.append(self.final_lexicon[p]['word'])
                
                if not part_words:
                    continue
                    
                # Join with Asian-style particle logic
                # Either direct concatenation or a soft glide
                if random.random() > 0.5:
                    joiner = ""
                else:
                    joiner = random.choice(PARTICLES)
                    
                unique_word = joiner.join(part_words)
                
                # Check collision on compound
                if unique_word in self.reverse_lookup:
                     unique_word = resolve_homonym(unique_word, self.reverse_lookup)

            if unique_word:
                self._register_word(stem, composition, unique_word)
                entry = dict(self.elemental_dict[key])
                entry['word'] = unique_word
                self.final_lexicon[key] = entry

    def save(self, filename='asian_conlang_lexicon.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.final_lexicon, f, indent=2, ensure_ascii=False)
        print(f"Saved to {filename}")

    def print_sample(self):
        print("\n--- SAMPLE DICTIONARY ---")
        items = list(self.final_lexicon.items())
        random.shuffle(items)
        for k, v in items[:20]:
            print(f"{k:<30} -> {v['word']:<20} (Spirit: {v.get('spirit', 'N/A')})")

    def generate(self):
        print("Generating Base Lexicon...")
        self.generate_base_lexicon()
        
        print("Generating Compounds...")
        self.generate_compounds()
        
        print("Resolving final collisions...")
        resolve_remaining_homonyms(self.final_lexicon, self.reverse_lookup)
        
        self.print_sample()
        self.save()

if __name__ == '__main__':
    # Ensure you have 'five_elements_dict.json' from the previous step
    input_file = 'five_elements_dict.json'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please run the previous script first.")
    else:
        with open(input_file, 'r', encoding='utf-8') as f:
            elemental_dict = json.load(f)

        generator = LexiconGenerator(elemental_dict)
        generator.generate()