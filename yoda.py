import nltk
from nltk import word_tokenize, pos_tag

# Ensure necessary NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt_tab')
    nltk.download('averaged_perceptron_tagger_eng')

def yoda_speak(sentence):
    """
    Translates a sentence into Yoda-speak (OSV order).
    """
    tokens = word_tokenize(sentence)
    tags = pos_tag(tokens)

    # Grammar to find the Main Verb Phrase
    grammar = r"""
        VP: {<MD>?<RB>*<VB.*>+} 
    """
    
    chunk_parser = nltk.RegexpParser(grammar)
    tree = chunk_parser.parse(tags)

    subject_parts = []
    verb_parts = []
    object_parts = []
    
    found_verb = False
    
    for subtree in tree:
        if type(subtree) == nltk.tree.Tree and subtree.label() == 'VP':
            verb_parts.extend([word for word, tag in subtree.leaves()])
            found_verb = True
        elif not found_verb:
            subject_parts.append(subtree[0])
        else:
            if subtree[0] not in ['.', '!', '?']:
                object_parts.append(subtree[0])

    # --- FIX START: Robust Case Cleaning ---
    def clean_case(text_list, is_start=False):
        # 1. Safety check for empty lists
        if not text_list:
            return ""
            
        text = " ".join(text_list)
        
        if is_start:
            return text[0].upper() + text[1:]
        else:
            first_word = text_list[0]
            # Don't lowercase "I" or proper nouns (heuristically capitalized words)
            if first_word != "I" and not first_word[0].isupper():
                 return text
            if first_word == "I": 
                return text
            # Lowercase the first letter
            return text[0].lower() + text[1:]
    # --- FIX END ---

    # Construct parts
    new_obj = clean_case(object_parts, is_start=True)
    new_subj = clean_case(subject_parts, is_start=False)
    new_verb = " ".join(verb_parts)

    # Assemble the final sentence dynamically to avoid extra commas/spaces
    # Standard Yoda: Object, Verb Subject.
    parts = []
    if new_obj:
        parts.append(f"{new_obj},")
    if new_verb:
        parts.append(new_verb)
    if new_subj:
        parts.append(new_subj)
        
    result = " ".join(parts)
    
    # Ensure it ends with punctuation
    if not result.endswith(('.', '!', '?')):
        result += "."
        
    return result

# --- Main Loop for Testing ---
if __name__ == "__main__":
    print("--- Yoda Translator (Type 'exit' to quit) ---")
    while True:
        user_input = input("Enter a sentence: ")
        if user_input.lower() == 'exit':
            break
        try:
            for sentance in nltk.sent_tokenize(user_input):
                print(yoda_speak(sentance))
        except Exception as e:
            print(f"Error: {e}")