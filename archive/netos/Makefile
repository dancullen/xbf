# Makefile contains all the commands to initialize your workspace, build the code, and run the tests.

.PHONY: help all info clean venv libs arm7 treck-libs snmp-libs app deploy

SCRIPTNAME := $(lastword $(MAKEFILE_LIST))
SCRIPTDIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

TOPDIR := $(SCRIPTDIR)/..
VENVDIR := $(SCRIPTDIR)/venv

ifeq ($(OS),Windows_NT)  # Windows 10 MSYS Git Bash shell
	PYTHON3_CMD := winpty /c/Python37/python.exe
	VENV_ACTIVATE := source $(VENVDIR)/Scripts/activate
else  # Linux shell
	PYTHON3_CMD := python3
	VENV_ACTIVATE := source $(VENVDIR)/bin/activate
endif


# Displays hints on how to to invoke this Makefile. This is the default target when you type 'make' without args.
help:
	@echo "See README.md for instructions."


# Invoking 'make all' builds a commonly-used subset of targets. It will also be used by the build server.
all: libs app


# Prints out Makefile variables, for official build logging and also for debugging.
info:
	@echo "SCRIPTNAME: $(SCRIPTNAME)"
	@echo "SCRIPTDIR:  $(SCRIPTDIR)"
	@echo "TOPDIR:     $(TOPDIR)"
	@echo "VENVDIR:    $(VENVDIR)"
	@echo "DEPLOYDIR:  $(DEPLOYDIR)"


# Deletes the artifacts generated from the 'libs' and 'app' targets.
# Does NOT delete $(VENVDIR) or $(DEPLOYDIR).
clean:
	cd $(TOPDIR)/netos/netos && make PLATFORM=connectcore9p9215_a clean
	cd $(TOPDIR)/netos/netos/src/examples/nasnmpv3/32b && make PLATFORM=connectcore9p9215_a clean


# Creates a Python virtual environment (venv) and installs all the tools and libraries inside it.
# Remarks:
# - Currently, this venv is used for the following purposes:
#   - To run our experiments in `aes.py`.
#   - To run our experiments with SNMPv3-Hash-Generator.
#   - To run the deployment script `deploy.py`.
# - CPython3 must already be installed on your system before invoking this target because it is required to generate the venv.
# - We generated requirements.txt like this: `python -m pip freeze > requirements.txt`.
venv:
	@echo "Checking for CPython3..."
	$(PYTHON3_CMD) --version
	@if [ -e $(VENVDIR) ] ; then echo "Cannot virtual environment; $(VENVDIR) already exists!" ; false ; fi
	$(PYTHON3_CMD) -m venv $(VENVDIR)
	$(VENV_ACTIVATE) && python -m pip install -r requirements.txt


# Builds all of the core Net+OS libraries for the ARM9 ConnectCore 9P 9215.
# Note that we need to build both the release and debug versions of the libraries
# because our 'nasnmpv3' test app links against some of each.
#
# Note that we're building with a single job (-j1) because I don't trust that the dependencies have
# been implemented correctly. (The app target, for example, fails intermittently with parallel jobs.)
libs:
	cd $(TOPDIR)/netos/netos && make PLATFORM=connectcore9p9215_a -j1
	cd $(TOPDIR)/netos/netos && make PLATFORM=connectcore9p9215_a DEBUG=on -j1


# This target builds the ARM7 version of the libraries.
# Digi WDS is not planning to test the ARM7 build-- customer said they will
# take responsibility for that testing-- but they want an ARM7 build as well
# in case they ever need to roll out the security updates to their older devices.
#
# Dave Ray figured out how to do this build on 2020-05-06.
#   "I just did a make PLATFORM=connectcore7u_a, which I gleaned from the Makefile.tools file.
#   The build then shows CPU=arm7 and PROCESSOR=ns7520 which they called out in the original SOW."
# Note that the Makefile.tools file includes `src/bsp/platforms/connectcore7u_a/Makefile.bsp`,
# which in turn sets CPU and PROCESSOR to the above.
arm7:
	cd $(TOPDIR)/netos/netos && make PLATFORM=connectcore7u_a -j1
	cd $(TOPDIR)/netos/netos && make PLATFORM=connectcore7u_a DEBUG=on -j1


# Builds all of the Treck libraries. Note that this includes the SNMP libraries.
#
# We created this target to allow us to build Treck's cryptlib and any other Treck
# libraries upon which the SNMP may depend. That way, if we modify the cryptlib functions,
# we can rebuild just the Treck libraries, not all of Net+OS, which is much faster.
#
# Note that even though the 'snmpd' folder lives within the src/treck folder,
# it is pretty much treated as its own project, separate from the other Treck sources.
# So it's not entirely surprising that invoking make in the treck project does NOT
# automatically build the SNMP libraries. Therefore, since we want our 'treck-libs' target below
# to build all Treck components, we must manually build the SNMP libraries after building
# the other Treck components-- hence the "$(MAKE) snmp-libs" command below. We do NOT add
# snmp-libs as a dependency of treck-libs because we want the SNMP libs to be built after
# (though it probably doesn't matter much because linking won't happen until the app is built).
treck-libs:
	cd $(TOPDIR)/netos/netos/src/treck && make PLATFORM=connectcore9p9215_a -j1 all
	cd $(TOPDIR)/netos/netos/src/treck && make PLATFORM=connectcore9p9215_a DEBUG=on -j1 all
	$(MAKE) snmp-libs


# Builds just the SNMP libs. We created a separate target for this because building all the libs every time takes forever.
# Here's how I determined the command that gets used to build: cd netos/netos && make PLATFORM=connectcore9p9215_a DEBUG=on VERBOSE=1 | tee dan.txt
snmp-libs:
	cd $(TOPDIR)/netos/netos/src/treck/snmpd && make PLATFORM="connectcore9p9215_a" ENDIAN="-mbig-endian" CPU="arm9" TOOLSET="gnu" CPU_FLAG="-mcpu=arm9tdmi" DEBUG="off" STACK="treck" -j1 all
	cd $(TOPDIR)/netos/netos/src/treck/snmpd && make PLATFORM="connectcore9p9215_a" ENDIAN="-mbig-endian" CPU="arm9" TOOLSET="gnu" CPU_FLAG="-mcpu=arm9tdmi" DEBUG="on"  STACK="treck" -j1 all


# Builds all SNMP example application code. Also copies the artifacts to the correct directory
# so that they can be downloaded to the target and executed.
#
# Be sure to define the required environment variables (e.g., in ~/.profile because it's an 'sh' shell)
# before running 'make app'. For example:
#   export DEPLOYDIR=/cygdrive/c/Users/dcullen/Documents/Digi_ESP/workspace_75/SNMP\ V3\ Sample/Debug
#
# IMPORTANT NOTE: Do not attempt to run the build with parallel jobs (e.g., -jN where N > 1).
# There is a race condition bug somewhere in the Makefiles (e.g., forgot to list a file dependency)
# which causes the build to intermittently fail with `./objs/appconf_api.o: no such file or directory`.
app:
	test -n "$(DEPLOYDIR)"  # Environment variable DEPLOYDIR must be defined.
	cd $(TOPDIR)/netos/netos/src/examples/nasnmpv3/32b && make PLATFORM="connectcore9p9215_a" ENDIAN="-mbig-endian" CPU="arm9" TOOLSET="gnu" CPU_FLAG="-mcpu=arm9tdmi" DEBUG="on" STACK="treck" -j1
	rm -f /cygdrive/c/Users/$(USER)/Documents/Digi_ESP/workspace_75/SNMP\ V3\ Sample/Debug/image.elf
	cp $(TOPDIR)/netos/netos/src/examples/nasnmpv3/32b/image.elf  "$(DEPLOYDIR)"


# Creates a zip file of the headers and build artifacts to give to the customer.
deploy:
	@echo "$(SCRIPTNAME): Deploying to zip file..."
	$(VENV_ACTIVATE) && python deploy.py
