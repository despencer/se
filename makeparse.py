#!/usr/bin/python3

import logging
import makelib as m

logging.basicConfig(filename='makefile.log', filemode='w', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

make = m.parse("/mnt/mobihome/sources/github/betaflight/betaflight/makefile")
print("Variables")
for v in sorted(make.variables.keys()):
    print(make.variables[v].formatverbose())

