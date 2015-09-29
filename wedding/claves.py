from random import choice, randint

def generar_claves():
    for number in xrange(100000,999999):
        yield str(number)

claves = [x for x in generar_claves()]

def generate_code():
    base = "%06d" % (randint(100000,999999),)
    letter = choice("abcdefghijklmnopqrstuvwxyz")
    position = randint(0, len(base))
    return letter.join((base[:position], base[position:]))
