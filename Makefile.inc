# Makefile.inc contains targets for working with Digi XBee 3 devices. "-include" this file in your top-level Makefile.

SHELL := /usr/bin/env bash  # https://stackoverflow.com/questions/7507810/how-to-source-a-script-in-a-makefile
MAKEFILENAME := $(lastword $(MAKEFILE_LIST))
MAKEFILEDIR := $(realpath $(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

ifndef TOPDIR
$(error TOPDIR environment variable is not set)
endif
ifndef DEPDIR
$(error DEPDIR environment variable is not set)
endif

BUILDDIR := $(TOPDIR)/build
LOGDIR := $(TOPDIR)/logs
VENVDIR := $(DEPDIR)/venv
XBFDIR := $(DEPDIR)/xbf

ifndef PYTHON3_CMD
$(error PYTHON3_CMD environment variable is not set)
# Recommend "python3" in Linux or "winpty /c/Python37/python.exe" in MS Windows MSYS Git Bash.
endif

ifeq ($(OS),Windows_NT)  # MS Windows MSYS Git Bash
	VENV_ACTIVATE := source $(VENVDIR)/Scripts/activate
	PATHSEP := ;
else  # Linux
	VENV_ACTIVATE := source $(VENVDIR)/bin/activate
	PATHSEP := :
endif

export PYTHONPATH=$(TOPDIR)$(PATHSEP)$(DEPDIR)$(PATHSEP)$(XBFDIR)/cpython/fakes$(PATHSEP)$(XBFDIR)/upython

help:
	@echo
	@echo "See README.md for instructions."
	@echo
	@echo "XBF environment info:"
	@echo
	@echo "  SHELL:         $(SHELL)"
	@echo "  MAKEFILENAME:  $(MAKEFILENAME)"
	@echo "  MAKEFILEDIR:   $(MAKEFILEDIR)"
	@echo "  TOPDIR:        $(TOPDIR)"
	@echo "  DEPDIR:        $(DEPDIR)"
	@echo "  BUILDDIR:      $(BUILDDIR)"
	@echo "  LOGDIR:        $(LOGDIR)"
	@echo "  VENVDIR:       $(VENVDIR)"
	@echo "  XBFDIR:        $(XBFDIR)"
	@echo "  PYTHON3_CMD:   $(PYTHON3_CMD)"
	@echo "  PYTHONPATH:    $(PYTHONPATH)"
	@echo

all: help

clean:
	rm -fr "$(BUILDDIR)" "$(LOGDIR)"

distclean: clean
	rm -fr "$(DEPDIR)"

# Creates a Python virtual environment and installs all tools and libraries inside it.
# CPython3 must be already installed because it is required to generate the virtual environment.
# Note that we generated requirements.txt like this: `python -m pip freeze > requirements.txt`
deps:
	mkdir -p "$(DEPDIR)"

	@echo "Checking for CPython3..."
	$(PYTHON3_CMD) --version
	@if [ -e $(VENVDIR) ] ; then echo "Cannot create virtual environment; $(VENVDIR) already exists!" ; false ; fi
	$(PYTHON3_CMD) -m venv "$(VENVDIR)"
	$(VENV_ACTIVATE) && python -m pip install -r "$(MAKEFILEDIR)"/requirements.txt

# Cross-compiles the MicroPython sources from .py to .mpy.
mpy:
	$(VENV_ACTIVATE) && python "$(XBFDIR)"/cpython/make.py --build

check-serial-opts:
ifndef PORT
	$(error PORT environment variable is not set)
endif
ifndef BAUD
	$(error BAUD environment variable is not set)
endif

# Deploys compiled MicroPython .mpy files to the XBee 3 device on a XBIB-U-DEV board connected via serial.
# Example usage: make deploy PORT=COM3 BAUD=115200
deploy: check-serial-opts
	$(VENV_ACTIVATE) && python "$(XBFDIR)"/cpython/make.py --build --deploy --port="$(PORT)" --baud="$(BAUD)"

# Runs the unit tests and all static analysis tools (pyflakes, flake8, pychecker, mypy, coverage, etc.).
test:
	$(VENV_ACTIVATE) && python "$(XBFDIR)"/cpython/test.py

.PHONY: help all clean distclean deps mpy deploy test
