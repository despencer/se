name1 := $(MAKEFILE_LIST)
name5 = $(MAKEFILE_LIST)
name6 := $(name1)
name7 = $(name1)
name8 := $(name5)
name9 = $(name5)
name10 ?= $(name1)
name11 ?= $(name5)
name12 ?= $(MAKEFILE_LIST)
name13 ?= $(name12)
ROOT  := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

a = a
b = $(a)
c = $(b)
name14 := $(c)
name14 := $(name14)d

ifeq "$(name5)" " makefile"
include $(ROOT)/inc3.mk
endif

include $(ROOT)/inc1.mk

name2 := $(MAKEFILE_LIST)

include $(ROOT)/sub/sub1.mk

name3 := $(MAKEFILE_LIST)

include $(ROOT)/inc1.mk

name4 := $(MAKEFILE_LIST)

include $(ROOT)/inc2.mk

name15 := $(patsubst ab,d,ab ac a b)
name16 := $(patsubst a%,d,ab ac a b)
name17 := $(patsubst a%,%d,ab ac a b za zaz)
name18 := $(patsubst a%b,%d,ab ac a b za zaz azab)
name19 := $(patsubst a,%d,ab ac a b)
name20 := $(patsubst ab%ba,c%c,abba aba a b)

all:
	@echo name1 = \'$(name1)\'
	@echo name2 = \'$(name2)\'
	@echo name3 = \'$(name3)\'
	@echo name4 = \'$(name4)\'
	@echo name5 = \'$(name5)\'
	@echo name6 = \'$(name6)\'
	@echo name7 = \'$(name7)\'
	@echo name8 = \'$(name8)\'
	@echo name9 = \'$(name9)\'
	@echo name10 = \'$(name10)\'
	@echo name11 = \'$(name11)\'
	@echo name12 = \'$(name12)\'
	@echo name13 = \'$(name13)\'
	@echo name14 = \'$(name14)\'
	@echo name15 = \'$(name15)\'
	@echo name16 = \'$(name16)\'
	@echo name17 = \'$(name17)\'
	@echo name18 = \'$(name18)\'
	@echo name19 = \'$(name19)\'
	@echo name20 = \'$(name20)\'

include $(ROOT)/inc3.mk