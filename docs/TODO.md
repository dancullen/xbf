# TODO

- Be sure to add any reusable code from xbgw to this project.

- Implement code to deploy .xpro and .ota files. See TODO items in make.py for details.

- OpenXBeeDevice should print serial port name that it's opening.

- Fakes / Mocks / Adapters
  - Two implementaions of cpython/xbee.py: 1) xbee-python implementation, 2) mock data implementation. (And then obviously there's 3) the micropython version that works on the real device.)
  - Two implementations of cpython/usocket.py: 1) CPython socket implementation, 2) mock data implementation. (And then obviously there's 3) icropython version that works on the real device.)

- Implement all the static analysis tools (e.g., pyflakes, etc.)
  recommended in the comments above 'test' target in Makefile.inc.

- Implement https://coverage.readthedocs.io/en/coverage-5.2.1/

- Implement an auto-formatter such as yapf.

- Figure out why address 0x0000000000000000 seems to send data to all nodes,
  not just to the coordinator, even though it is listed under "unicast transmission"
  on this page: https://www.digi.com/resources/documentation/Digidocs/90001942-13/Default.htm#concepts/c_transmission_methods_zigbee.htm

- Consolidate code in 'archive' as well as code from CSXB (particularly 
  `arch/common/networking.py`, `arch/micropython/test/test_xbee3*.py`,
  and `arch/cpython3/test/*.py`).

- Add user data relay logging demo from the CSXB MicroPython app!
