.. Seed Auth API documentation master file, created by
   sphinx-quickstart on Wed May 11 15:21:20 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Seed Auth API's documentation!
=========================================

Contents:

.. toctree::
   :maxdepth: 2

   http_api


Overview
^^^^^^^^
Seed Auth was designed to allow one or more applications to be able to delegate authentication and user and permission management to a single, internal service. For the case of multiple applications, this avoids the need for users to authenticate separately for each application.

An application would use Seed Auth as follows:

   1. Permissions are added to teams of users in Seed Auth, where each permission could be an application-specific permission, or a :ref:`permission relevant to Seed Auth <permissions>`.
   2. An authentication token is acquired for a user in Seed Auth.
   3. When a client sends a request to an application, the application makes a request to Seed Auth using the authentication token given in the client's request's ``Authorization`` header, and is given back the permissions granted to the authenticated user. The user's permissions are used by the application to determine whether the user has access to the requested resource.


::

   client ------------------> application ----------------> seed-auth-api

           GET /things/23                  Get /user
           Authorization: Token 1234       Authorization: Token 1234

          <------------------             <---------------

             {id: '23'}                   {
                                            ...
                                            permissions: [{
                                              namespace: 'app:foo',
                                              type: 'thing:read',
                                              object_id: '23'
                                            }]
                                          }


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

