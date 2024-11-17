
.. _`wire`:

Wire Interface
==============

This page documents the inner API of the ``AuthWire[T]`` interface.
Any class extending the interface should implement the two following functions :

#. ``def encode (obj: T) -> JsonType``
#. ``def decode (obj: JsonType) -> T``

These methods should be inverses of each other and should implement a way to 
translate from a python object of type ``T`` to a json object and the same backwards.
