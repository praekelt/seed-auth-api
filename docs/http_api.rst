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


.. _permissions:

While you can store any string as a permission, there are a few permissions
that have specific meaning within the Seed Auth API.

Create permissions are not linked to a specific instances, where as admin, read,
and write permissions are.

A user automatically has read/write permissions for themselves, without being
in a team that grants those permissions.

admin
    Full create/read/write permissions.
org:create
    Can create new organizations.
org:admin
    Can create/read/write users and teams, and can add users to the
    organization that they are an admin for. Can read/write the organization
    that they are admin for.
org:write
    Can modify an organization's details, including adding existing users and
    teams to the organization.
org:read
    Can view an organization's details.
team:create
    Can create new teams.
team:admin
    Can read/write the specific team. Can create and add users to the team that
    they are admin for.
team:write
    Can modify the team they have permission for, including adding or removing
    permissions, and adding existing users to the team.
team:read
    Can view the group they have permission for.
user:create
    Can create new users.
user:write
    Can modify the user they have the permission for.
user:read
    Can read the user data they have the permission for.


.. _tokens:

Tokens
^^^^^^

For the token endpoints, no authentication is required.

.. http:post:: /tokens/create

   Create a new token for the provided user.

   :<json str username: The username of the user to create the token for.
   :<json str password: The password of the user to create the token for.
   :>json str token: The generated token.
   :status 201: When the token is successfully generated.
   :status 400: When the user credentials are incorrect.

   **Example request**:

   .. sourcecode:: http

      POST /tokens/create HTTP/1.1
      Content-Type: application/json

      {"username":"testuser","password":"testpassword"}

   
   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Content-Type: application/json

      {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"}


.. http:post:: /tokens/verify

   Verify that an existing token is valid, and return the token's payload.

   :<json str token: The token to verify.
   :>json obj payload: The payload of the token.
   :status 200: The token is valid.
   :status 400: The token is invalid.

   **Example request**:

   .. sourcecode:: http
   
      POST /tokens/verify HTTP/1.1
      Content-Type: application/json

      {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"}

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {"payload":{"sub":"1234567890","name":"John Doe","admin":true}}
