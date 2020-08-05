# Design Rationales

Q: Why did we implement TCP and UDP in MicroPython?

A: The IPv4 API Frames don't support reliability/acks. More generally, the API Frames protocol
   doesn't support reliability/acks. So if packets are lost, we would have know way of knowing.
   So we rolled out our own custom reliability protocol on top of User Data Relay API Frames.
   Another solution might have been to use the new Sockets API Frames, but that feature wasn't added
   to the XBee until much later into the project. Since we have lots of control over the sockets with
   the MicroPython code, and we already had a good framework in place for our own application-layer
   messages on top of User Data Relay API frames, and since the xbee-ansic-library (a.k.a. XBCLIB)
   is so cumbersome to use, we opted to continue down the route of the User Data Relay approach
   instead of the Sockets API Frames approach.
