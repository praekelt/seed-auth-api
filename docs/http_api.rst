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

All users have read permissions for all other users, and organizations.

All members of an organization have read access to that organization's teams.


org:admin
    Can create/read/write/delete users, and teams that are part of the
    organization, and can add users to the organization that they are an admin
    for. Can read/write the organization that they are admin for.
org:write
    Can modify an organization's details, including adding existing users and
    teams to the organization.
team:write
    Can modify the team they have permission for, including adding or removing
    permissions, and adding existing users to the team.
team:read
    Can view the team they have permission for.
user:create
    Can create new users.


.. _tokens:

Tokens
^^^^^^

For the token endpoints, no authentication is required.

.. http:post:: /tokens/

   Create a new token for the provided user.

   :<json str username: The username of the user to create the token for.
   :<json str password: The password of the user to create the token for.
   :>json str token: The generated token.
   :status 201: When the token is successfully generated.
   :status 400: When the user credentials are incorrect.

   **Example request**:

   .. sourcecode:: http

      POST /tokens/ HTTP/1.1
      Content-Type: application/json

      {"username":"testuser","password":"testpassword"}

   
   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Content-Type: application/json

      {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"}


.. http:get:: /token

   Verify that an existing token is valid, and return the token's payload.

   :>header Authorization: "JWT " followed by the token to verify
   :>json obj payload: The payload of the token.
   :status 200: The token is valid.
   :status 400: The token is invalid.

   **Example request**:

   .. sourcecode:: http
   
      GET /token HTTP/1.1
      Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {"payload":{"sub":"1234567890","name":"John Doe","admin":true}}


Password resets
^^^^^^^^^^^^^^^

For the password reset endpoints, no authentication is required.

To reset a user's password, the following steps should be followed:

1. Make a request to the reset endpoint.
   This will make an HTTP request to the preconfigured endpoint with the user's
   details, and a token.
2. Make a request to the confirm endpoint, with the provided token and the new
   password.

.. http:post:: /passwords/resets/

   Start the process for resetting a user's password.

   :<json str username: The username of the user to reset the password for.
   :<json str app:
        The application that the token should go to, configured in settings.
   :code 202: The password reset process was started.
   :code 400: The username does not exist.

   **Example request**:

   .. sourcecode:: http

      POST /passwords/resets/ HTTP/1.1
      Content-Type: application/json

      {"username":"jonsnow","app":"numi"}

   **Example response**:

   .. sourcecode:: http
      
      HTTP/1.1 202 Accepted

.. http:post:: /passwords/confirmations/

   Reset the users password using the provided token.

   :<json str token: The provided token.
   :<json str password: The new password.
   :code 200: The password was successfully reset.
   :code 400: The token was incorrect.

   **Example request**:

   .. sourcecode:: http

      POST /password/confirmations/ HTTP/1.1
      Content-Type: application/json

      {"password":"gh0st","token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvbiBTbm93In0.H7huFJ_ioqf1-_qzZQ6VLHOJpnqhdDiZFV2VdkIt7LY"}

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
