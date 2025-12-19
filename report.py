# Load elemental_dict.json
# Iterate through entries
# Create totals for composition elements
# Show totals and averages for each of the elements

import json
from collections import Counter
import matplotlib.pyplot as plt

data = json.load(open("elemental_dict.json","r", encoding='utf-8'))

elements = { 'earth':0,'fire':0,'water':0,'air':0}
for row in data:
    for el in elements:
        elements[el]+=data[row]['composition'][el]

lin = len(data)
for el in elements:
    print(el,":",elements[el],":",elements[el]/lin)

freqs = {el: Counter() for el in elements}
for row in data:
    comp = data[row].get('composition', {})
    for el in elements:
        v = comp.get(el, 0)
        try:
            v = int(v)
        except Exception:
            v = 0
        if v < 0:
            v = 0
        if v > 64:
            v = 64
        freqs[el][v] += 1

x = list(range(0, 65))
fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True, sharey=True)
axes = axes.flatten()

for ax, el in zip(axes, ['earth', 'air', 'water', 'fire']):
    y = [freqs[el].get(i, 0) for i in x]
    ax.bar(x, y)
    ax.set_title(el)
    ax.set_xlabel('value')
    ax.set_ylabel('count')

plt.tight_layout()
plt.savefig('element_frequency.png', dpi=200)
plt.show()