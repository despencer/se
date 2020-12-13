#!/usr/bin/python3

import logging
import makelib as m

logging.basicConfig(filename='makefile.log', filemode='w', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

m.parse("/mnt/mobihome/sources/github/betaflight/betaflight/makefile")

