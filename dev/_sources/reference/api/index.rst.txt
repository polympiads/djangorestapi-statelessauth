
.. _`api`:

API Reference
=============

This page documents the inner API of the ``statelessauth`` project. The project is separated into the following modules (all relative to ``rest_framework_statelessauth``).

#. :ref:`Wire <wire>` - ``.wire`` : responsible for encoding and decoding objects from and to JSON.
#. :ref:`Engine <engine>` - ``.engine`` : contains the different engines for the encoding and decoding as well as views.
#. :ref:`Middlewares <middleware>` - ``.middlewares`` : contains the authentication middleware.
#. :ref:`Config <config>` - ``.config`` : contains the configuration utils.

It also contains the following implementations

#. :ref:`User Auth <user>` - ``.contrib.auth`` : Implementation of the default django authentication system

We will be using the following guidelines regarding the documentation :

#. Whenever a generic class is used, we will write ``class A[T]`` instead of ``class A(Generic[T])``, where ``T`` is a ``TypeVar`` as defined by Python's ``typing`` module.
#. Whenever a generic class is used with a type containing a bound on it, we will write ``class A[T extends B]``, where ``B`` must be an ancestor of ``T``. It is defined as ``class A(Generic[T])``, where ``T`` is a ``TypeVar`` with ``bound=B`` as defined by Python's ``typing`` module.

.. toctree::
   :hidden:

   wire
   engine
   middleware
   config
   user