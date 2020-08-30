# Demo: An example project

This directory demonstrates how to set up a project that uses the xbf library.

## Getting Started

To get started, simply type `make bootstrap` then `make deps`.
This downloads xbf and sets up the virtual environment.

Note that this clones a copy of the `xbf` repo into its `deps` folder. Yes it seems
a bit meta / recursive,  but it's more illustrative of how you'd be doing this in a
real project-- i.e., from a separate repo, outside the xbf project.

## Technical Details

To prevent errors when running Make before downloading the xbf dependency, you must do the following:

- Make the "-include" statement optional by prefixing it with a "-".

- Invoke targets from Makefile.inc directly via "$(MAKE") rather than listing them than as dependencies
  of targets in this Makefile (e.g., can't do "unittest: test"; instead use "unittest:\n\t@$(MAKE) test").

These tricks allow us to bootstrap our dev environment using this Makefile rather than a separate shell script.

Note that Makefile.inc includes some commonly-used targets such as 'build', 'clean', 'test', etc.
What if you want to use one of these names in your top-level project? The answer is to simply create
a new target with a new, distinct name, such as 'build-project'. The reason we did not prefix or suffix
the targets in Makefile.inc with "xbf" (e.g., 'xbf-build', 'clean-xbf', etc.) is for simplicity-- we do not
want the top-level Makefile to have to re-implement and invoke all the `*xbf*` targets. Since this framework
is for MicroPython projects, it is probably very rare that the user would want to redefine these targets.
For example, it is unlikely that the user would need to redefine the 'build' target to build other things as well.
And if they do need to build other things, 1) they can simply call their new target something else, or 2) they can
do it in a totally separate Makefile for a totally separate area of the project (because chances are it would be
for building code for some other language entirely like C or C++).
