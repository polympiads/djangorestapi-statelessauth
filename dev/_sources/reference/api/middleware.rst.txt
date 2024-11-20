:tocdepth: 4

.. _`middleware`:

Authentication Middleware
=========================

The authentication middleware is a simple django middleware that relies entirely on the list of sub middlewares
provided by the configuration. Each sub middleware contains an engine, a field in request and a header.
They work in the following way :

#. The header is a tuple representing header name (like ``"Authorization"``) and expected prefix inside the header (like ``"Bearer"``). If the prefix is empty, then only the token should be in the header value, otherwise we expects the header value to contain the prefix, a space and the token value.
#. If the header isn't present then the sub middleware is skipped.
#. Once we have extracted the token, it is decoded and verified through the authentication engine.
#. If anything has failed in this step, then an error (likely 403) will be raised.
#. Otherwise, we set the field in the request to be the decoded value.

.. toctree::
   :hidden:

   