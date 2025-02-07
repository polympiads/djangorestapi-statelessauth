:tocdepth: 4

.. _`engine`:

Authentication Engines
======================

This page documents the inner API of the ``AuthEngine[T]`` interface, and its default implementations.
It contains the following modules

#. :ref:`.engine.abstract <abstract_engine>` - Module responsible for the abstract authentication engine interface
#. :ref:`.engine.acquire <acquire_engine>` - Module responsible for the classical authentication engine with an acquire view
#. :ref:`.engine.refresh <refresh_engine>` - Module responsible for refreshable authentication engine with an acquire and a refresh view

.. _abstract_engine:

Module ``.engine.abstract``
---------------------------

This module contains a single class, the abstract authentication engine.
The purpose of an authentication engine is to define properly how to encode
the different tokens.

``class AuthEngine[T]``
~~~~~~~~~~~~~~~~~~~~~~~

This class implements the default functions an authentication engine should
provide, as well as different tools to generate the tokens properly.

constructor ``__init__(self, keyname, scheme, algorithms)``
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

This constructor defines an authentication engine by providing the key name,
linking it through the configuration. One also needs to provide the algorithms
used to encode and decode the tokens, the first element of this list being how it
is encoded. All of them are used to decode the tokens. By default it is ``[ 'RS256' ]``.
Finally, one needs to provide the scheme used to transform the data into json, it
needs to be an ``AuthWire[T]`` 

property ``key``
""""""""""""""""

Returns the key used for encrypting / decrypting the tokens.
By default, goes through the configuration to retrieve the key
from its name, and if it has been set, the key will be the one
provided to bypass configuration.

property ``urlpatterns``
""""""""""""""""""""""""

Defines a set of urls used for authentication.
For example, it can be used to acquire a token or to refresh it.

method ``headers(self, data)``
"""""""""""""""""""""""""""""""""""""""""""""

Defines a way for sub classes to define the JWS headers. By default, return ``{}``.

method ``payload_from_wired(self, wired)``
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Defines how to go from the encoded value (wired) to the payload, allows the sub class
to add custom properties to the payload. By default, returns ``wired``.

method ``wired_from_payload(self, payload)``
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Defines how to go from the payload to the encoded value (wired), allows the sub class
to remove the custom properties it has added. By default, returns ``payload``.

method ``validate_payload (self, payload)``
"""""""""""""""""""""""""""""""""""""""""""

This method is to validate the payload, for example if it had a timeout, it returns whether the deadline
isn't yet over. By default, returns ``True``.

method ``encode(self, data)``
"""""""""""""""""""""""""""""

Encodes the data of type ``T`` into a signed json web token by first
transforming it into its wired form and then its payload form. 

method ``decode(self, token, verify, return_payload)``
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Decodes the data by first verifying its signature and that the payload is valid.

#. By default ``verify`` is ``True``, and any error raise ``JWSError``, otherwise in case of an error it returns ``None``.
#. By default ``return_payload`` is ``False``, and it only checks the signature and returns the payload if it is ``True``.


.. _acquire_engine:

Module ``.engine.acquire``
--------------------------

This module defines the class ``AcquireEngine[T]``.
It takes in its constructor the same data as the abstract
authentication engine and a function that takes the same arguments
as a django view but should return either ``None`` or an object of
type ``T``. This view represents how a user acquires an authentication
token with type ``T``. It then implements the true django view
``acquire_view`` that wraps your view, and define a urlpattern at
``acquire/`` that you can find in the ``urlpatterns`` method.

.. _refresh_engine:

Module ``.engine.refresh``
--------------------------

This module defines the class ``RefreshEngine[T]``,
which is equivalent in behaviour as ``AcquireEngine[T]``,
except that every token has a short time expiration date,
and a long time expiration date, that you can configure with the 
two parameters at the end of the constructor in this order.

The payload is considered valid if the short expiration date hasn't
yet expired.
It defines a new view ``refresh_view`` allowing you to refresh the
short time and long time expiration dates if the long one hasn't expired.
This view is exposed at the url ``refresh/`` in ``urlpatterns``. The
class also overrides the ``wired_from_payload`` and ``payload_from_wired``
methods.

.. toctree::
   :hidden:

   