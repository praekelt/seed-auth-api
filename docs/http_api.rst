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


