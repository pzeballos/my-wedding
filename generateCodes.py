from random import shuffle, choice
vocal = "aeiou"
cons = "bcdfgjklmnprstvwxyz"

claves = []
for i in xrange(500):
    first = ["a", "v"]
    shuffle(first)
    
    for l in range(10):
        if l == 0:
            pwd = first.pop()
            nextVowel = pwd == 'a'
        elif l == 5:
            pwd += first[0]
        else:
            s = nextVowel and vocal or cons
            pwd += choice(s)
        nextVowel = not nextVowel
    claves.append(pwd)

print "claves =",
print claves
