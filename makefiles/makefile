name1 := $(MAKEFILE_LIST)
ROOT  := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT)/inc1.mk

name2 := $(MAKEFILE_LIST)

include $(ROOT)/sub/sub1.mk

name3 := $(MAKEFILE_LIST)

include $(ROOT)/inc1.mk

name4 := $(MAKEFILE_LIST)

all:
	@echo name1 = \'$(name1)\'
	@echo name2 = \'$(name2)\'
	@echo name3 = \'$(name3)\'
	@echo name4 = \'$(name4)\'