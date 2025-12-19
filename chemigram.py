import json
import itertools
from collections import Counter

def find_elemental_anagrams(filepath):
    try:
        with open(filepath, 'r') as f:
            lexicon = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    # Map words to their elemental composition values
    # Using a tuple of sorted values as the key to identify anagrams
    # Values: (Air, Water, Earth, Fire)
    anagram_groups = {}
    
    for entry_id, data in lexicon.items():
        if "composition" in data and "word" in data:
            comp = data["composition"]
            # Extract the 4 values and sort them to create a canonical key
            values = sorted([
                comp.get("air", 0),
                comp.get("water", 0),
                comp.get("earth", 0),
                comp.get("fire", 0)
            ])
            key = tuple(values)
            
            if key not in anagram_groups:
                anagram_groups[key] = []
            
            # Store word and its original mapping for comparison
            anagram_groups[key].append({
                "translation": entry_id,
                "word": data["word"],
                "definition": data.get("definition", ""),
                "composition": comp
            })

    # Filter to only groups with more than one word (true anagrams)
    found_anagrams = {str(k): v for k, v in anagram_groups.items() if len(v) > 1}
    return found_anagrams

def print_results(results):
    if not results:
        print("No elemental anagrams found.")
        return

    last = ""
    for words, key in enumerate(results):
        if key != last:
            print(key)
        for word in results[key]:
            s = word['translation']
            print(word['translation'])
            # print(key,':',word['word'],':',s,':',word['definition'])
        last=key

if __name__ == "__main__":
    results = find_elemental_anagrams('conlang_lexicon.json')
    print_results(results)