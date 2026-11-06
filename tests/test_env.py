"""Gate: the stack we depend on imports on this interpreter."""

import sys


def test_python_and_stack():
    assert sys.version_info >= (3, 14)
    import aiortc
    import av
    import slixmpp

    assert aiortc.__version__
    assert av.__version__
    assert slixmpp.__version__
