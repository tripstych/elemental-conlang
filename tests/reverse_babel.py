import json
import os
import re
import sys


class ReverseConlangTranslator:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.word_to_entries = {}
        for key, entry in lexicon.items():
            if not isinstance(entry, dict):
                continue
            word = entry.get('word')
            if not word:
                continue
            self.word_to_entries.setdefault(word, []).append(
                {
                    'key': key,
                    'definition': entry.get('definition', ''),
                    'composition': entry.get('composition', {}),
                }
            )

    @classmethod
    def from_json(cls, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        return cls(lexicon)

    def translate_word(self, token):
        entries = self.word_to_entries.get(token)
        if not entries:
            return None
        return entries

    def translate_text(self, text):
        tokens = re.findall(r"[\w']+|[^\w\s]", text, flags=re.UNICODE)
        out = []
        for t in tokens:
            if t.isspace():
                out.append(t)
                continue
            if re.match(r"^[\w']+$", t, flags=re.UNICODE):
                entries = self.translate_word(t)
                if not entries:
                    out.append(f"[{t}]")
                    continue

                best = entries[0]
                out.append(best['key'])
            else:
                out.append(t)
        return " ".join(out).replace("  ", " ")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lexicon_path = os.path.join(base_dir, 'conlang_lexicon.json')

    if not os.path.exists(lexicon_path):
        print(f"CRITICAL ERROR: {lexicon_path} not found.")
        print("Run logo_gene.py first to generate conlang_lexicon.json")
        return

    translator = ReverseConlangTranslator.from_json(lexicon_path)
    print(f"Reverse dictionary loaded: {len(translator.word_to_entries)} conlang wordforms")
    print("Type conlang text to translate. Enter blank line or 'quit' to exit.")

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    while True:
        try:
            line = input('> ')
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line.strip() or line.strip().lower() == 'quit':
            break

        tokens = re.findall(r"[\w']+|[^\w\s]", line.strip(), flags=re.UNICODE)
        for tok in tokens:
            if not re.match(r"^[\w']+$", tok, flags=re.UNICODE):
                continue
            entries = translator.translate_word(tok)
            if not entries:
                print(f"{tok} -> [unknown]")
                continue

            if len(entries) == 1:
                e = entries[0]
                d = e['definition']
                if d:
                    print(f"{tok} -> {e['key']} :: {d}")
                else:
                    print(f"{tok} -> {e['key']}")
                continue

            print(f"{tok} -> {len(entries)} matches")
            for i, e in enumerate(entries[:10], 1):
                d = e['definition']
                if d:
                    print(f"  {i}. {e['key']} :: {d}")
                else:
                    print(f"  {i}. {e['key']}")


if __name__ == '__main__':
    main()
