.. _http-api:


HTTP API
========

Seed Auth's HTTP API.


.. _authentication:

Authentication
^^^^^^^^^^^^^^
Authentication is done via JSON Web Token (JWT) token authentication.
The tokens endpoint can be used to create a token. The token can then
be placed in the header for requests to the other endpoints.

**Example request**:

.. sourcecode:: http
   
   POST /endpoint/ HTTP/1.1
   Content-Type: application/json
   Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"


