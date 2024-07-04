

from patchbook import patchParser
x = patchParser()
x.parseFile('Examples/patch1.txt')
x.printConnections()

x.parseFile('diatom-patches/052023.txt')
x.printConnections()
