# Makefile contains all the commands to initialize your workspace, build the code, and run the tests.

MAKEFILENAME := $(lastword $(MAKEFILE_LIST))
MAKEFILEDIR := $(realpath $(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
TOPDIR := $(MAKEFILEDIR)
DEPDIR := $(TOPDIR)/deps

-include deps/xbf/Makefile.inc

bootstrap:
	mkdir -p "$(DEPDIR)"

	cd "$(DEPDIR)" &&\
	git clone git@github.com:dancullen/xbf.git &&\
	cd xbf &&\
	git fetch --tags --force &&\
	git checkout master

	@$(MAKE) xbf-deps

unittest:
	@$(MAKE) test
	$(VENV_ACTIVATE) && python "$(TOPDIR)"/cpython/test.py

main-cpython:
	$(VENV_ACTIVATE) && python "$(TOPDIR)"/cpython/main.py

main-upython:
	@$(MAKE) deploy PORT=COM4 BAUD=115200

.PHONY: bootstrap unittest main-cpython main-upython
