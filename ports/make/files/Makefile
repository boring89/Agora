# STELA port test for GNU make.
SHELL := /Data/Programs/dash/bin/dash
WORDS := one two three
all: count
	@echo "make: built $(words $(WORDS)) words"
count: /tmp/make-a.txt
	@echo "make: count $$(cat /tmp/make-a.txt 2>/dev/null || echo 1)"
/tmp/make-a.txt:
	@echo "make: making $@"
	@echo 1 > $@
