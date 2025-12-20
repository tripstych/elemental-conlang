import random
import operator
import json
import math
import sys
import argparse

# --- 1. PHONETIC ENGINE ---

class PhoneticEngine:

# ... inside PhoneticEngine class ...

    def __init__(self, config_path='phonetic_dictionary.json'):
        self.config = self._load_config(config_path)
        
        # 1. Phonemes
        self.onset_phones = self.config.get('onset_phones', {})
        self.nucleus_vowels = self.config.get('nucleus_vowels', {})
        self.nucleus_modifiers = self.config.get('nucleus_modifiers', {})
        self.coda = self.config.get('coda', {})
        
        # 2. Phonotactic Templates
        self.templates = self.config.get('templates', {
            'default': ["ONK", "ONM", "ONK NM"]
        })

        # 3. Morphology
        self.morphology = self.config.get('morphology', {
            'connectors': ["a'", "e'", "i'"],
            'suffixes': ['os', 'ix', 'ul', 'ym'],
            'compound_strategies': ['connector', 'suffix', 'both']
        })

        self.constraints = self.config.get('constraints', [])
        self.orthography = self.config.get('orthography', [])

    def _is_valid(self, word):
        """Checks word against all regex constraints."""
        for rule in self.constraints:
            pattern = rule.get('pattern')
            if re.search(pattern, word):
                # print(f"Rejected '{word}': {rule.get('reason')}") # Debugging
                return False
        return True

    def _apply_orthography(self, word):
        """Applies spelling rules in order."""
        out = word
        for rule in self.orthography:
            src = rule.get('from')
            dest = rule.get('to')
            out = out.replace(src, dest)
        return out

    # UPDATE THIS METHOD
    def construct_word(self, pos, vector, reverse_lookup):
        # ... (Context setup same as before) ...
        
        # CONTEXT SETUP
        sorted_elements = sorted(vector.items(), key=operator.itemgetter(1), reverse=True)
        primary = sorted_elements[0][0] if sorted_elements else 'air'
        secondary = sorted_elements[1][0] if len(sorted_elements) > 1 else primary
        
        context = {'pos': pos, 'primary': primary, 'secondary': secondary}
        template_list = self.templates.get(pos, self.templates.get('default'))

        # ATTEMPT GENERATION
        for _ in range(50): # Increased attempts to account for rejections
            template = random.choice(template_list)
            raw_word = self._generate_from_template(template, context)
            
            # 1. CHECK CONSTRAINTS
            if not self._is_valid(raw_word):
                continue

            # 2. APPLY ORTHOGRAPHY
            polished_word = self._apply_orthography(raw_word)

            # 3. CHECK UNIQUENESS
            if len(polished_word) > 1 and polished_word not in reverse_lookup:
                return polished_word
        
        # Fallback (Make sure fallback passes orthography too!)
        fallback = self._generate_from_template("ONKNM", context)
        return self._apply_orthography(fallback)

    def _load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._get_default_config()

    def _get_default_config(self):
        # Fallback defaults if JSON is missing
        return {
            'onset_phones': {'n': ['d', 'z', 'n', 'l', 'r'], 'v': ['t', 'p', 'k']},
            'nucleus_vowels': {'fire': ['a', 'ay'], 'air': ['e', 'eo'], 'earth': ['i', 'ia'], 'water': ['u', 'ua']},
            'coda': {'fire': ['z', 'st'], 'air': ['th', 'ft'], 'earth': ['rd', 'rn'], 'water': ['m', 'l']},
            'nucleus_modifiers': {'n': ['w', 'r'], 'v': ['j', 'n']},
            'templates': {'default': ["ONK", "ONM"]}
        }

    def _resolve_symbol(self, symbol, context):
        """
        Maps a single character token (O, N, K, M) to a specific sound.
        """
        pos = context['pos']
        primary = context['primary']
        secondary = context['secondary']

        options = []
        
        if symbol == 'O': # Onset (based on POS)
            options = self.onset_phones.get(pos, self.onset_phones.get('n', []))
            
        elif symbol == 'N': # Nucleus (based on Primary Element)
            options = self.nucleus_vowels.get(primary, self.nucleus_vowels.get('air', []))
            
        elif symbol == 'K': # Coda (based on Secondary Element)
            options = self.coda.get(secondary, self.coda.get('air', []))
            
        elif symbol == 'M': # Modifier (based on POS)
            options = self.nucleus_modifiers.get(pos, self.nucleus_modifiers.get('n', []))
            
        elif symbol == ' ': # Literal space
            return ''
        else:
            # Literal character
            return symbol

        if not options:
            return ''
        
        return random.choice(options)

    def _generate_from_template(self, template, context):
        """Parses a template string like 'ONK' and builds the word."""
        word_parts = []
        for char in template:
            sound = self._resolve_symbol(char, context)
            word_parts.append(sound)
        return "".join(word_parts)

    def construct_word(self, pos, vector, reverse_lookup):
        """
        Selects a template and attempts to build a unique word.
        """
        # 1. Determine Context
        sorted_elements = sorted(vector.items(), key=operator.itemgetter(1), reverse=True)
        # Default to 'air' if vector is empty or issues arise
        primary = sorted_elements[0][0] if sorted_elements else 'air'
        
        if len(sorted_elements) > 1 and sorted_elements[1][1] > 0:
            secondary = sorted_elements[1][0]
        else:
            secondary = primary
        
        context = {
            'pos': pos,
            'primary': primary,
            'secondary': secondary
        }

        # 2. Select Template List
        template_list = self.templates.get(pos, self.templates.get('default'))
        if not template_list:
            template_list = ["ONK"] # Absolute fallback

        # 3. Attempt Generation
        for _ in range(20): 
            template = random.choice(template_list)
            candidate = self._generate_from_template(template, context)
            
            if len(candidate) > 1 and candidate not in reverse_lookup:
                return candidate
        
        # Fallback if unique generation failed
        fallback = self._generate_from_template("ONKNM", context)
        return fallback

    def assemble_compound(self, parts, strategy=None):
        if not parts:
            return None

        connectors = self.morphology.get('connectors', ["'"])
        suffixes = self.morphology.get('suffixes', [])
        strategies = self.morphology.get('compound_strategies', ['connector'])

        if not strategy:
            strategy = random.choice(strategies)

        if strategy == 'connector':
            glue = random.choice(connectors)
            return glue.join(parts)
        
        elif strategy == 'suffix':
            base = "".join(parts)
            tail = random.choice(suffixes) if suffixes else ""
            return f"{base}{tail}"
            
        elif strategy == 'both':
            glue = random.choice(connectors)
            base = glue.join(parts)
            tail = random.choice(suffixes) if suffixes else ""
            return f"{base}{tail}"
            
        else:
            return "".join(parts)

    def resolve_homonym(self, word, reverse_lookup):
        # Strategy A: Scramble Middle
        candidate = self._scramble_internal(word)
        if candidate and candidate not in reverse_lookup:
            return candidate
            
        # Strategy B: Swap Vowel
        candidate = self._swap_vowel(word)
        if candidate and candidate not in reverse_lookup:
            return candidate
            
        return None 

    def _scramble_internal(self, word):
        if len(word) < 4: return None
        mid = list(word[1:-1])
        random.shuffle(mid)
        return word[0] + "".join(mid) + word[-1]

    def _swap_vowel(self, word):
        vowels = 'aeiou'
        chars = list(word)
        for i, c in enumerate(chars):
            if c in vowels:
                if random.random() > 0.5:
                    chars[i] = random.choice([v for v in vowels if v != c])
                    return "".join(chars)
        return None


# --- 2. LEXICON GENERATOR ---

class LexiconGenerator:
    def __init__(self, elemental_dict, phonetic_engine, wordlist_path='words.txt', output_path='conlang_lexicon.json'):
        self.elemental_dict = elemental_dict
        self.engine = phonetic_engine
        self.wordlist_path = wordlist_path
        self.output_path = output_path
        
        self.final_lexicon = {}
        self.reverse_lookup = set()
        
        self.stem_index = {}
        for key in self.elemental_dict:
            stem = key.split('.')[0]
            self.stem_index.setdefault(stem, []).append(key)
        self.compound_keys = [k for k in self.elemental_dict if '_' in k]

    def generate(self):
        print(f"   - Processing {len(self.elemental_dict)} entries...")
        print("1. Generating Base Words...")
        self._generate_base()
        
        print("2. Generating Compounds...")
        self._generate_compounds()
        
        self.save()

    def _generate_base(self):
        count = 0
        for key, data in self.elemental_dict.items():
            if '_' in key: continue # Skip compounds
            
            # Safe parsing of POS
            parts = key.split('.')
            pos = parts[1] if len(parts) > 1 else 'n'
            
            vec = data.get('composition', {})
            
            word = self.engine.construct_word(pos, vec, self.reverse_lookup)
            
            if not word: 
                continue 
            
            self.final_lexicon[key] = {**data, 'word': word}
            self.reverse_lookup.add(word)
            count += 1
        print(f"   - Created {count} base words")

    def _generate_compounds(self):
        count = 0
        for key in self.compound_keys:
            stem = key.split('.')[0]
            parts_keys = self._find_compound_parts(stem)
            
            if not parts_keys: continue
            
            part_words = []
            valid = True
            for pk in parts_keys:
                if pk in self.final_lexicon:
                    part_words.append(self.final_lexicon[pk]['word'])
                else:
                    valid = False
                    break
            
            if not valid: continue

            compound_word = self.engine.assemble_compound(part_words)

            if compound_word in self.reverse_lookup:
                resolved = self.engine.resolve_homonym(compound_word, self.reverse_lookup)
                if resolved:
                    compound_word = resolved
                else:
                    continue 

            self.final_lexicon[key] = {
                **self.elemental_dict[key], 
                'word': compound_word
            }
            self.reverse_lookup.add(compound_word)
            count += 1
        print(f"   - Created {count} compounds")

    def _find_compound_parts(self, stem):
        raw_parts = stem.split('_')
        resolved_keys = []
        for p in raw_parts:
            if p in self.stem_index:
                # Naive strategy: grab the first variant found (usually noun 01)
                resolved_keys.append(self.stem_index[p][0])
        return resolved_keys if len(resolved_keys) == len(raw_parts) else None

    def save(self):
        print(f"Saving {len(self.final_lexicon)} words to {self.output_path}...")
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.final_lexicon, f, indent=2, ensure_ascii=False)


# --- 3. MAIN EXECUTION ---

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a conlang lexicon')
    parser.add_argument('--elemental-dict', default='elemental_dict.json')
    parser.add_argument('--phonetic-dict', default='phonetic_dictionary.json')
    parser.add_argument('--wordlist', default='words.txt')
    parser.add_argument('--output', default='conlang_lexicon.json')
    args = parser.parse_args()

    print(f"--- Conlang Generator Started ---")

    print(f"[1/4] Initializing Phonetic Engine from '{args.phonetic_dict}'...")
    phonetic_engine = PhoneticEngine(config_path=args.phonetic_dict)
    
    print(f"[2/4] Loading Elemental Dictionary from '{args.elemental_dict}'...")
    try:
        with open(args.elemental_dict, 'r', encoding='utf-8') as f:
            elemental_dict = json.load(f)
    except Exception as e:
        print(f"Error loading elemental dictionary: {e}")
        sys.exit(1)

    print(f"[3/4] Initializing Generator...")
    generator = LexiconGenerator(
        elemental_dict=elemental_dict, 
        phonetic_engine=phonetic_engine, 
        wordlist_path=args.wordlist,
        output_path=args.output
    )

    print(f"[4/4] Generating Lexicon...")
    generator.generate()
    
    print(f"--- Done ---")