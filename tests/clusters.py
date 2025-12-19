f = open("words.txt")
words = f.readlines()
words = [word.strip("\n") for word in words]

vowels = ['a','e','i','o','u','y']
sets = {}
for word in words:
    if len(word)<2:
        continue
    last = word[-1]
    snd = word[-2]
    if last not in vowels and snd not in vowels:
        sets[snd+last] = snd+last


sets = dict(sorted(sets.items()))


print(sets)