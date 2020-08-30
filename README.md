# XBee Framework (XBF)

A reference design for Digi XBee 3 MicroPython-based development.

Despite the coincidental similarity in name, this project is NOT the same as the
"XBee Application Framework (XAF)" for the Digi Connect Port line of products.

## Getting Started

To use this framework in your own project: see `demo/README.md` and `demo/Makefile`.

To work on developing the xbf library: see this library's unit tests, located in `cpython/test.py`.
The target `test` in `Makefile.inc` is responsible for executing these tests. You can invoke them
by running `make test` in the `demo` directory (after following the setup directions in `demo/README.md`).
