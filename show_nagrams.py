import json
from collections import defaultdict

# Load the dictionary
words = json.load(open("slim_dictionary.json"))

# Group keys by the sorted characters of their values
anagrams = defaultdict(list)

for key, value in words.items():
    # Create a signature by sorting the characters in the value string
    signature = "".join(sorted(value))
    anagrams[signature].append(key+':'+value)

grams = {}
for sig in anagrams:
    if len(anagrams[sig])>1:
        grams[sig] = anagrams[sig]


# Output the result
print(json.dumps(grams, indent=2))

