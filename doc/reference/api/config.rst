:tocdepth: 4

.. _`config`:

Configuration
=============

The configuration is separated into three parts :

#. Key backends - Stored in ``SL_AUTH_KEY_BACKENDS``, it should be a dictionary containing keys from the ``python-jose`` package. 
#. Authentication Engines - Stored in ``SL_AUTH_ENGINES``, it should be a dictionary containing the authentication engines.
#. Sub middlewares - Stored in ``SL_AUTH_MIDDLEWARES``, it should be a dictionary containing sub middlewares configurations.

A sub middleware configuration is a dictionary with any of the three following entries :

#. ``engine`` - The name of the engine, which will be looked up inside the ``SL_AUTH_ENGINES`` table.
#. ``header`` - The header in which the token should be.
#. ``field`` - The field in which the resulted value should be stored.

The behaviour of these fields is explained in the :ref:`middleware section <middleware>`.

Example
-------

One example of a possible configuration is the following :

.. code-block:: python
    :emphasize-lines: 4,7,11,12,13,14,15

    SIMPLE_PRIVATE_KEY = ...

    SL_AUTH_KEY_BACKENDS = {
        "default": RSAKey( SIMPLE_PRIVATE_KEY, 'RS256' )
    }
    SL_AUTH_ENGINES = {
        "default": RefreshEngine( "default", UserWire(), user_acquire_view )
    }

    SL_AUTH_MIDDLEWARES = {
        "auth": {
            "engine" : "default",
            "header" : ("Authorization", "Bearer"),
            "field"  : "user"
        }
    }

It describes a configuration similar to the default authentication of django.
This example is minimal, and here, you would miss the url patterns that you can add in the following way :

.. code-block:: python
    :emphasize-lines: 1,4

    engine = StatelessAuthConfig.instance().get_engine("default")

    urlspatterns = [
        path("api/account/", include(engine.urlpatterns))
    ]

You would also need to add the authentication middleware in the following way to your configuration :

.. code-block:: python
    :emphasize-lines: 1,3

    MIDDLEWARE = [
        # ... other middlewares
        "rest_framework_statelessauth.middleware.AuthMiddleware"
    ]

.. toctree::
   :hidden:

   