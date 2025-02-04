
.. _`user`:

Authentication Application
==========================

This page documents the inner API of the ``.contrib.auth`` package, defining an interface
similar to the one provided by default by the ``django.contrib.auth`` model. It defines
objects that are detached from a database, but contain the same data as the models inside
the django data, such as ``User``, ``Group`` and ``Permission`` as well as a way to go
from the database to the detached model using the ``User.from_user``, ``Group.from_group``
and ``Permission.from_permission`` static methods.

It also defines ``AuthWire`` implementations for all of the three object types, as well
as an acquire view, ``user_acquire_view``, that allows a user to login through GET parameters and retrieve an
authorization token for later use.
