import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
import json

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--filename", default="translation", help="Input file name")
args = parser.parse_args()

with open(args.filename, "r", encoding="utf-8", errors="replace") as f:
    lexicon = f.readlines()


tokes = []
for lex in lexicon:
    for toke in lex.split(" "):
        if len(toke)>1:
            tokes.append(toke)

# 1. Assume 'tokens' is a list of your words/runes
# Example: tokens = ["urg", "zia", "urg", "kran", "tee", "urg" ...]
counts = Counter(tokes)
frequencies = sorted(counts.values(), reverse=True)
ranks = range(1, len(frequencies) + 1)

# 2. Convert to log scale
log_ranks = np.log10(ranks)
log_freqs = np.log10(frequencies)

# 3. Plotting
plt.figure(figsize=(10, 6))
plt.scatter(log_ranks, log_freqs, alpha=0.5)
plt.title("Zipf's Law Test")
plt.xlabel("Log(Rank)")
plt.ylabel("Log(Frequency)")

# 4. Fit a line to see the slope
m, b = np.polyfit(log_ranks, log_freqs, 1)
plt.plot(log_ranks, m*log_ranks + b, color='red', label=f'Slope: {m:.2f}')
plt.legend()
plt.show()

print(f"Calculated Alpha (Slope): {abs(m)}")