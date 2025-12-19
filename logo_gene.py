import random
import operator
import json
import math
import os
import re


# --- 1. STRICT RUNIC CONFIGURATION (No Gemination/Double Letters) ---

# CHANGES:
# 1. Removed doubled vowels (aa, ee, ii) -> Replaced with Diphthongs (ia, eo, io).
#    (Runes do not double letters for length. 'aa' is strictly incorrect orthography).
# 2. Removed 'll' in modifiers -> Replaced with 'lr'.
# 3. Maintained 'ae', 'oe', 'ng', 'th' as they represent SINGLE distinct runes (Ash, Odal, Ingwaz, Thurisaz).

onset_phones = {
    # Nouns: Heavy clusters (Kn- / Gn- / Wr-)
    'n': [
        'd', 'z', 'n', 'l', 'r',             
        'dr', 'dw',
        'gr', 'gl', 'gn', 'gw',              
        'k', 'kr', 'kl', 'kw',              
        'br', 'bl', 'bn',                    
        'wr'
    ], 
    
    # Verbs: Sharp/Percussive
    'v': [
        't', 'p', 'k',                       
        'tr', 'tw',                          
        'pr', 'pl',                          
        'sk', 'sp', 'st',                    
        'skr', 'spr', 'str'                  
    ],           
    
    # Adjectives: Fricatives/Breathy
    'a': [
        'f', 's', 'h', 'ᚦ',                 
        'fl', 'fr', 'hl', 
        'br', 'bl', 'ᚦr', 'ᚦw'                         
    ],          
    
    'e': ['f', 'h', 'hw', 'ᚦ'], 
    'r': ['j', 'w', 'm'], 
    's': ['f', 'j', 'z', 'ᚦ'],
    'k': ['g', 'k', 'kw'],
    'i': ['b', 'f', 'm'],
    'd': ['th', 'd', 'dh'], 
    'o': ['h', 'w'], 
}

nucleus_vowels = {
    # Fire: Bright/High
    # Replaced 'ii' (Double) with 'io' (Diphthong)
    'fire':  ['a', 'ay', 'ah', 'oa', 'ya', 'ia', 'ua'],   
    
    # Air: Mid
    # Replaced 'ee' (Double) with 'eo' (Valid Runic Diphthong)
    'air':   ['e', 'eo', 'ei', 'ae', 'ee', 'ey'],  
    
    # Earth: Low/Back
    # Replaced 'aa' (Double) with 'ia' (Diphthong)
    'earth': ['i', 'ia', 'iu', 'io', 'iy'],  
    
    # Water: Round/Deep
    # 'uo' and 'ou' are valid diphthongs, not doubles
    'water': ['u', 'ui', 'uu', 'ua', 'ue']    
}

nucleus_modifiers = {
    'n': ['w', 'u', 'r', 'l'], 
    'v': ['j', 'i', 'n'],      
    'a': ['h', 'w'],           
    'e': ['h'],
    
    # Replaced 'll' (Double) with 'lr' (Liquid Cluster)
    'r': ['l', 'r', 's'],
    
    's': ['z'],
    'k': ['n', 'ng'],
    'i': ['w'],
    'd': ['j'],
    'o': ['h'],
}

coda = {
    'earth': [
         'rb', 'rc', 'rf', 'rg', 'rm', 'rn', 'rp,' 'rs' 'rst', 
    ], 
    'air':   [ 
        'ft', 'ht', 'lt', 'nt', 'rt','st'
    ],
    'fire':  [
        'ks', 'k', 'z', 'sk', 'st']
    , 
    'water': ['m', 'l', 'n', 'ng', 'rm', 'rn'] 
}
# --- 2. CORE GENERATOR FUNCTIONS ---

def to_rune(text):

    rune_map = {
        'th': '', 'ng': 'ᛜ', 'ae': 'ᚫ', 'oe': 'ᛟ', 'ea': 'ᛠ', 'eo': 'ᛇ',
        'ei': 'ᛇ', 'au': 'ᚢ', 'aa': 'ᚪ', 'ks': 'ᛉ',
        'a': 'ᚨ', 'b': 'ᛒ', 'c': 'ᚲ', 'd': 'ᛞ', 'e': 'ᛖ', 'f': 'ᚠ',
        'g': 'ᚷ', 'h': 'ᚺ', 'i': 'ᛁ', 'j': 'ᛃ', 'k': 'ᚲ', 'l': 'ᛚ',
        'm': 'ᛗ', 'n': 'ᚾ', 'o': 'ᛟ', 'p': 'ᛈ', 'r': 'ᚱ', 's': 'ᛋ',
        't': 'ᛏ', 'u': 'ᚢ', 'v': 'ᚠ', 'w': 'ᚹ', 'y': 'ᛃ', 'z': 'ᛉ'
    }
 
    rune_map = {
        'th': 'ᚦ', 'ng': 'ᛜ', 'ae': 'ᚫ', 'oe': 'ᛟ', 'ea': 'ᛠ', 'eo': 'e',
        'ei': 'ᛇ', 'au': 'ᚢ', 'aa': 'ᚪ', 'ks': 'ᛉ',
        'a': 'a', 'b': 'ᛒ', 'c': 'ᚲ', 'd': 'ᛞ', 'e': 'ᛖ', 'f': 'ᚠ',
        'g': 'ᚷ', 'h': 'ᚺ', 'i': 'ᛁ', 'j': 'ᛃ', 'k': 'ᚲ', 'l': 'ᛚ',
        'm': 'ᛗ', 'n': 'ᚾ', 'o': 'ᛟ', 'p': 'ᛈ', 'r': 'ᚱ', 's': 'ᛋ',
        't': 'ᛏ', 'u': 'ᚢ', 'v': 'v', 'w': 'w', 'y': 'ᛃ', 'z': 'ᛉ'
    }
    
    # Simple replacement (Order matters! Digraphs first)
    out = text.lower()
    for k in ['th', 'ng', 'ae', 'oe', 'ea', 'eo', 'ei', 'au', 'aa', 'ks']:
        out = out.replace(k, rune_map[k])
    for k in rune_map:
        if len(k) == 1:
            out = out.replace(k, rune_map[k])
    return out

def mutate_vector(vector):
    elements = ['earth','air','fire','water']
    for element in elements:
        vector[element] = min(0, max(64, vector[element]+random.randint(-10,10)))
    return vector

def construct_word(pos, vector, reverse_lookup):
    sorted_elements = sorted(vector.items(), key=operator.itemgetter(1), reverse=True)
    primary = sorted_elements[0][0]
    
    # Secondary influence for Coda
    if len(sorted_elements) > 1 and sorted_elements[1][1] > 0:
        secondary = sorted_elements[1][0]
    else:
        secondary = primary

    sound_onset = random.choice(onset_phones[pos])
    sound_vowel = random.choice(nucleus_vowels[primary])
    sound_coda = random.choice(coda[secondary])
    test = f"{sound_onset}{sound_vowel}{sound_coda}"
    if test not in reverse_lookup:
        return test
    sound_glide = random.choice(nucleus_modifiers[pos])
    test = f"{sound_onset}{sound_vowel}{sound_glide}"
    if test not in reverse_lookup:
        return test
    sound_vowel_2 = random.choice(nucleus_vowels[primary])

    return f"{sound_onset}{sound_vowel}{sound_coda}{sound_vowel_2}{sound_glide}"

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
    """Returns True if vectors are semantically close (synonyms)."""
    dist = 0
    for k in ['fire', 'water', 'air', 'earth']:
        v1 = vec1.get(k, 0)
        v2 = vec2.get(k, 0)
        dist += (v1 - v2) ** 2
    return math.sqrt(dist) < threshold

def composition_signature(composition):
    return (
        composition.get('fire', 0),
        composition.get('water', 0),
        composition.get('air', 0),
        composition.get('earth', 0),
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

# --- 4. MAIN EXECUTION ---

import itertools

def generate_digraph_anagrams(word):
    digraphs = ['th', 'dh', 'ae', 'oe', 'ea', 'au', 'ou', 'uo', 'ng', 'ie', 'ei', 'aa']
    # Sort digraphs by length descending to match longest first
    sorted_digraphs = sorted(digraphs, key=len, reverse=True)
    
    tokens = []
    i = 0
    while i < len(word):
        match_found = False
        for dg in sorted_digraphs:
            if word.startswith(dg, i):
                tokens.append(dg)
                i += len(dg)
                match_found = True
                break
        if not match_found:
            tokens.append(word[i])
            i += 1
            
    # Generate unique permutations of the tokens
    perms = set(itertools.permutations(tokens))
    return ["".join(p) for p in perms]

def _build_phoneme_units():
    units = set()
    for pos in onset_phones:
        units.update(onset_phones[pos])
    for element in nucleus_vowels:
        units.update(nucleus_vowels[element])
    for pos in nucleus_modifiers:
        units.update(nucleus_modifiers[pos])
    for element in coda:
        units.update(coda[element])
    return units

def tokenize_phonemes(word, phoneme_units=None):
    if phoneme_units is None:
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

def _build_vowel_pool():
    pool = set()
    for element in nucleus_vowels:
        pool.update(nucleus_vowels[element])
    return sorted(pool, key=len, reverse=True)

def scramble_preserving_ends(word, reverse_lookup, attempts=250, phoneme_units=None):
    tokens = tokenize_phonemes(word, phoneme_units=phoneme_units)
    if len(tokens) <= 2:
        return None
    if len(tokens) == 3:
        candidate = "".join([tokens[0], tokens[1], tokens[2]])
        if candidate not in reverse_lookup:
            return candidate
        return None

    first = tokens[0]
    last = tokens[-1]
    middle = tokens[1:-1]
    if len(middle) <= 1:
        return None

    seen = set()
    for _ in range(attempts):
        mid = middle[:]
        random.shuffle(mid)
        key = tuple(mid)
        if key in seen:
            continue
        seen.add(key)
        candidate = "".join([first] + mid + [last])
        if candidate not in reverse_lookup:
            return candidate
    return None

def swap_vowels_preserving_ends(word, reverse_lookup, attempts=250, phoneme_units=None, vowel_pool=None):
    if vowel_pool is None:
        vowel_pool = _build_vowel_pool()
    vowel_set = set(vowel_pool)

    tokens = tokenize_phonemes(word, phoneme_units=phoneme_units)
    if len(tokens) <= 2:
        return None

    eligible = [i for i, t in enumerate(tokens) if 0 < i < len(tokens) - 1 and t in vowel_set]
    if not eligible:
        return None

    for _ in range(attempts):
        new_tokens = tokens[:]
        swap_count = 1
        if len(eligible) > 1:
            swap_count = random.randint(1, min(2, len(eligible)))
        for idx in random.sample(eligible, swap_count):
            current = new_tokens[idx]
            options = [v for v in vowel_pool if v != current]
            if not options:
                continue
            new_tokens[idx] = random.choice(options)
        candidate = "".join(new_tokens)
        if candidate not in reverse_lookup:
            return candidate
    return None

def resolve_homonym(word, reverse_lookup, scramble_attempts=250, vowel_attempts=250, phoneme_units=None, vowel_pool=None):
    candidate = scramble_preserving_ends(
        word,
        reverse_lookup,
        attempts=scramble_attempts,
        phoneme_units=phoneme_units,
    )
    if candidate:
        return candidate
    return swap_vowels_preserving_ends(
        word,
        reverse_lookup,
        attempts=vowel_attempts,
        phoneme_units=phoneme_units,
        vowel_pool=vowel_pool,
    )

def resolve_remaining_homonyms(final_lexicon, reverse_lookup):
    phoneme_units = _build_phoneme_units()
    vowel_pool = _build_vowel_pool()

    word_to_keys = {}
    for k, entry in final_lexicon.items():
        w = entry.get('word')
        if not w:
            continue
        word_to_keys.setdefault(w, []).append(k)

    for w, keys in word_to_keys.items():
        if len(keys) <= 1:
            continue

        stems = {}
        for k in keys:
            stem = k.split('.')[0]
            stems.setdefault(stem, []).append(k)
        if len(stems) <= 1:
            continue

        kept = False
        kept_sigs = set()
        for stem, stem_keys in stems.items():
            if not kept:
                kept = True
                for k in stem_keys:
                    comp = final_lexicon[k].get('composition', {})
                    kept_sigs.add(composition_signature(comp))
                continue
            for k in stem_keys:
                comp = final_lexicon[k].get('composition', {})
                if composition_signature(comp) in kept_sigs:
                    continue
                new_word = resolve_homonym(
                    w,
                    reverse_lookup,
                    phoneme_units=phoneme_units,
                    vowel_pool=vowel_pool,
                )
                if not new_word:
                    continue
                final_lexicon[k]['word'] = new_word
                reverse_lookup.add(new_word)


class LexiconGenerator:
    """Generate a conlang lexicon from elemental_dict.json.

    Generation pipeline:
    1) Generate base (non-compound) entries.
    2) Generate compound entries using already-generated base wordforms.
    3) Resolve remaining homonyms (composition-aware).
    """

    def __init__(self, elemental_dict):
        self.elemental_dict = elemental_dict

        self.stem_index = {}
        for key in self.elemental_dict:
            stem = key.split('.')[0]
            self.stem_index.setdefault(stem, []).append(key)

        self.final_lexicon = {}
        self.reverse_lookup = set()
        self.word_compositions = {}
        self.stem_history = {}
        self.compound_keys = []

    def _register_word(self, stem, composition, word):
        self.reverse_lookup.add(word)
        self.word_compositions.setdefault(word, set()).add(composition_signature(composition))
        self.stem_history.setdefault(stem, []).append((composition, word))

    def _rebuild_state_from_lexicon(self):
        self.reverse_lookup = set()
        self.word_compositions = {}
        self.stem_history = {}

        for k, entry in self.final_lexicon.items():
            w = entry.get('word')
            if not w:
                continue
            stem = k.split('.')[0]
            comp = entry.get('composition', {})
            self.reverse_lookup.add(w)
            self.word_compositions.setdefault(w, set()).add(composition_signature(comp))
            self.stem_history.setdefault(stem, []).append((comp, w))

    def _generate_base_word(self, stem, pos, composition):
        unique_word = None

        if stem in self.stem_history:
            for prev_vector, prev_word in self.stem_history[stem]:
                if vectors_match(composition, prev_vector):
                    unique_word = prev_word
                    break

        if unique_word is not None:
            return unique_word

        max_retries = 20
        for _ in range(max_retries):
            candidate = construct_word(pos, composition, self.reverse_lookup)

            if candidate not in self.reverse_lookup:
                return candidate

            sig = composition_signature(composition)
            if sig in self.word_compositions.get(candidate, set()):
                return candidate

            resolved = resolve_homonym(candidate, self.reverse_lookup)
            if resolved:
                return resolved

        return None

    def _random_composition(self):
        composition = {
            'air': random.randint(0, 64),
            'water': random.randint(0, 64),
            'earth': random.randint(0, 64),
            'fire': random.randint(0, 64),
        }
        if sum(composition.values()) == 0:
            composition[random.choice(['air', 'water', 'earth', 'fire'])] = 1
        return composition

    def _generate_word_with_length(self, pos, composition, min_len, max_len, attempts=200):
        sorted_elements = sorted(composition.items(), key=operator.itemgetter(1), reverse=True)
        primary = sorted_elements[0][0] if sorted_elements else 'air'
        if len(sorted_elements) > 1 and sorted_elements[1][1] > 0:
            secondary = sorted_elements[1][0]
        else:
            secondary = primary

        onset_options = [''] + onset_phones.get(pos, onset_phones['n'])
        vowel_options = nucleus_vowels.get(primary, nucleus_vowels['air'])
        coda_options = [''] + coda.get(secondary, coda['air'])
        glide_options = [''] + nucleus_modifiers.get(pos, nucleus_modifiers['n'])

        sig = composition_signature(composition)
        for _ in range(attempts):
            onset = random.choice(onset_options)
            vowel = random.choice(vowel_options)
            tail = random.choice([0, 1, 2])
            if tail == 0:
                suffix = random.choice(coda_options)
            elif tail == 1:
                suffix = random.choice(glide_options)
            else:
                suffix = random.choice([random.choice(coda_options), random.choice(glide_options)])

            candidate = f"{onset}{vowel}{suffix}"
            if not (min_len <= len(candidate) <= max_len):
                continue
            if candidate not in self.reverse_lookup:
                return candidate
            if sig in self.word_compositions.get(candidate, set()):
                return candidate

        return None

    def _next_available_key(self, stem, pos):
        sense = 1
        while True:
            key = f"{stem}.{pos}.{sense:02d}"
            if key not in self.final_lexicon:
                return key
            sense += 1

    def _get_stem_word(self, stem):
        noun_key = None
        any_key = None
        prefix = f"{stem}."
        for k in self.final_lexicon:
            if not k.startswith(prefix):
                continue
            if any_key is None:
                any_key = k
            if '.n.' in k:
                noun_key = k
                break

        chosen = noun_key or any_key
        if not chosen:
            return None
        entry = self.final_lexicon.get(chosen, {})
        return entry.get('word')

    def _add_filler_base_entry(self, stem, existing_stems, pos='n'):
        if stem in existing_stems:
            return True

        composition = self._random_composition()
        unique_word = self._generate_base_word(stem, pos, composition)
        if unique_word is None:
            return False

        self._register_word(stem, composition, unique_word)
        key = self._next_available_key(stem, pos)
        self.final_lexicon[key] = {
            'composition': composition,
            'definition': '',
            'word': unique_word,
        }
        self.stem_index.setdefault(stem, []).append(key)
        existing_stems.add(stem)
        return True

    def fill_missing_from_wordlist(self, filename='words.txt'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(base_dir, filename)
        if not os.path.exists(filename):
            return

        existing_stems = {k.split('.')[0] for k in self.final_lexicon}
        with open(filename, 'r', encoding='utf-8') as f:
            for raw_line in f:
                raw = raw_line.strip().lower()
                if not raw:
                    continue

                cleaned = re.sub(r"[^a-z\s_\-]", "", raw)
                stem = re.sub(r"[\s\-]+", "_", cleaned).strip('_')
                if not stem or stem in existing_stems:
                    continue

                parts = [p for p in stem.split('_') if p]
                if len(parts) >= 2:
                    for p in parts:
                        if p not in existing_stems:
                            ok = self._add_filler_base_entry(p, existing_stems, pos='n')
                            if not ok:
                                parts = None
                                break
                    if not parts:
                        continue

                    part_words = []
                    missing_part = False
                    for p in parts:
                        w = self._get_stem_word(p)
                        if not w:
                            missing_part = True
                            break
                        part_words.append(w)
                    if missing_part:
                        continue

                    composition = self._random_composition()
                    max_retries = 20
                    unique_word = None
                    for attempt in range(max_retries):
                        candidate = random.choice(["a'", "e'", "i'"]).join(part_words)
                        if attempt > 0:
                            candidate += random.choice(['os', 'ix', 'ul', 'ym'])

                        if candidate not in self.reverse_lookup:
                            unique_word = candidate
                            break

                        sig = composition_signature(composition)
                        if sig in self.word_compositions.get(candidate, set()):
                            unique_word = candidate
                            break

                        resolved = resolve_homonym(candidate, self.reverse_lookup)
                        if resolved:
                            unique_word = resolved
                            break

                    if unique_word is None:
                        continue

                    self._register_word(stem, composition, unique_word)
                    key = self._next_available_key(stem, 'n')
                    self.final_lexicon[key] = {
                        'composition': composition,
                        'definition': '',
                        'word': unique_word,
                    }
                    self.stem_index.setdefault(stem, []).append(key)
                    existing_stems.add(stem)
                    continue

                self._add_filler_base_entry(stem, existing_stems, pos='n')

    def optimize_short_word_translations(self, filename='words.txt'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(base_dir, filename)
        if not os.path.exists(filename):
            return

        short_stems = set()
        with open(filename, 'r', encoding='utf-8') as f:
            for raw_line in f:
                raw = raw_line.strip().lower()
                if not raw:
                    continue
                cleaned = re.sub(r"[^a-z\s_\-]", "", raw)
                stem = re.sub(r"[\s\-]+", "_", cleaned).strip('_')
                if stem and len(stem) < 4 and '_' not in stem:
                    short_stems.add(stem)

        for k, entry in self.final_lexicon.items():
            stem = k.split('.')[0]
            if stem not in short_stems:
                continue
            current = entry.get('word')
            if not current:
                continue

            n = len(stem)
            min_len = max(1, n - 1)
            max_len = n + 1
            if min_len <= len(current) <= max_len:
                continue

            parts = k.split('.')
            pos = parts[1] if len(parts) > 1 else 'n'
            composition = entry.get('composition', {})
            candidate = self._generate_word_with_length(pos, composition, min_len, max_len)
            if candidate:
                entry['word'] = candidate

        self._rebuild_state_from_lexicon()

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
        for key in self.compound_keys:
            stem = key.split('.')[0]
            composition = self.elemental_dict[key].get('composition', {})

            parts = assemble_compound(stem, self.stem_index, self.elemental_dict)
            if not parts:
                continue

            max_retries = 20
            unique_word = None
            for attempt in range(max_retries):
                part_words = []
                missing_part = False
                for p in parts:
                    p_entry = self.final_lexicon.get(p)
                    if not p_entry:
                        missing_part = True
                        break
                    w = p_entry.get('word')
                    if not w:
                        missing_part = True
                        break
                    part_words.append(w)
                if missing_part:
                    break

                candidate = random.choice(["a'", "e'", "i'"]).join(part_words)
                if attempt > 0:
                    candidate += random.choice(['os', 'ix', 'ul', 'ym'])

                if candidate not in self.reverse_lookup:
                    unique_word = candidate
                    break

                sig = composition_signature(composition)
                if sig in self.word_compositions.get(candidate, set()):
                    unique_word = candidate
                    break

                resolved = resolve_homonym(candidate, self.reverse_lookup)
                if resolved:
                    unique_word = resolved
                    break

            if unique_word is None:
                continue

            self._register_word(stem, composition, unique_word)

            entry = dict(self.elemental_dict[key])
            entry['word'] = unique_word
            self.final_lexicon[key] = entry

    def resolve_homonyms(self):
        resolve_remaining_homonyms(self.final_lexicon, self.reverse_lookup)

    def print_stats(self):
        print(f"Total Definitions: {len(self.elemental_dict)}")
        unique_word_pairs = {
            (entry.get('word'), composition_signature(entry.get('composition', {})))
            for entry in self.final_lexicon.values()
            if entry.get('word')
        }
        print(f"Total Unique Words: {len(unique_word_pairs)}")

        compounds = [k for k in self.final_lexicon if '_' in k]
        print(f"\nSample Compounds ({len(compounds)} found):")
        for k in compounds[:15]:
            print(f"{k} -> {self.final_lexicon[k]['word']}")

    def save(self, filename='conlang_lexicon.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.final_lexicon, f, indent=2, ensure_ascii=False)

    def generate(self):
        print("Generating Lexicon...")
        self.generate_base_lexicon()

        print("Generating Compounds...")
        self.generate_compounds()

        self.fill_missing_from_wordlist('words.txt')

        self.optimize_short_word_translations('words.txt')

        self.resolve_homonyms()

        self.print_stats()
        self.save()
        return self.final_lexicon


if __name__ == '__main__':
    with open('elemental_dict.json', 'r', encoding='utf-8') as f:
        elemental_dict = json.load(f)

    generator = LexiconGenerator(elemental_dict)
    generator.generate()