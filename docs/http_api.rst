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

Permissions
^^^^^^^^^^^

While you can store any string as a permission, there are a few permissions
that have specific meaning within the Seed Auth API.

Create permissions are not linked to specific instances, whereas admin, read,
and write permissions are.

A user automatically has read/write permissions for themselves.

All users have read permissions for all users and organizations.

All members of an organization have read access to that organization's teams.

Permissions can be assigned either to a user or a team. All users can add and
remove permissions for all teams and users, except for the following
permissions, which can only be set be set by a person with org:admin
permission.


org:admin
    Can create/read/write/delete users, and teams that are part of the
    organization, and can add users to the organization that they are an admin
    for. Can read/write the organization that they are admin for.
org:write
    Can modify an organization's details, including adding existing users and
    teams to the organization.
team:admin
    Can modify the team they have permission for, and add and remove existing
    users to that team.
team:read
    Can view the team they have permission for.
user:create
    Can create new users.


.. _pagination:

Pagination
^^^^^^^^^^

When the results set is larger than a configured amount, the data is broken up
into pages.

You can navigate to specific pages using the 'page' parameter. Links to the
next and previous page (if available) will be provided in the 'Link' header.

Example:

.. sourcecode:: http

   GET /endpoint/ HTTP/1.1
   Authorization: JWT .....


   HTTP/1.1 200 OK
   Content-Type: application/json
   Link: <https://example.com/endpoint/?page=2>; rel="next"

   [....]

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

   :<json str email: The email of the user to reset the password for.
   :<json str app:
        The application that the token should go to, configured in settings.
        This value is optional, defaults to the default configured application.
   :code 202:
        The password reset process was started, or the username doesn't exist.
        The same code is returned for both as to not leak user information

   **Example request**:

   .. sourcecode:: http

      POST /passwords/resets/ HTTP/1.1
      Content-Type: application/json

      {"email":"jonsnow@castleblack.org","app":"numi"}

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted

.. http:post:: /passwords/confirmations/

   Reset the users password using the provided token.

   :<json str token: The provided token.
   :<json str password: The new password.
   :code 204: The password was successfully reset.
   :code 400: The token was incorrect.

   **Example request**:

   .. sourcecode:: http

      POST /password/confirmations/ HTTP/1.1
      Content-Type: application/json

      {"password":"gh0st","token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvbiBTbm93In0.H7huFJ_ioqf1-_qzZQ6VLHOJpnqhdDiZFV2VdkIt7LY"}

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content


Organizations
^^^^^^^^^^^^^

Organizations provide a grouping of users, although users do not have to belong
to an organization, and they can also belong to many organizations. Teams have
to belong to exactly one organization, but an organization can have many teams.

.. http:post:: /organizations/

    Creates a new organization.

    :>json str name: The name of the created organization.
    :>json int id: The id of the created organization.
    :>json list teams: The list of teams that the organization has.
    :>json list users: The list of users that are part of the organization.
    :status 201: When the organization is successfully generated.
    :status 400: When there is invalid information to create the organization.

    **Example request**:

    .. sourcecode:: http

       POST /organizations/ HTTP/1.1
       Content-Type: application/json

       {"name":"Nights Watch"}


    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {"name":"Nights Watch","id":4,"teams":[],"url":"https://example.org/organizations/4","users":[]}

.. http:get:: /organizations/

    Get a list of existing organizations

    **Example request**:

    .. sourcecode:: http

       GET /organizations/ HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       [{"name":"Nights Watch","id":4,"teams":[],"url":"https://example.org/organizations/4","users":[]}]

.. http:get:: /organizations/(int:organization_id)

    Get the details of an organization.

    :>json str name: The name of the created organization.
    :>json int id: The id of the created organization.
    :>json list teams: The list of teams that the organization has.

    **Example request**:

    .. sourcecode:: http

       GET /organizations/4 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {"name":"Night's Watch","id":4,"teams":[],"url":"https://example.org/organizations/4","users":[]}

.. http:put:: /organizations/(int:organization_id)

    Update an existing organization.

    :<json str name: The name of the organization.
    :>json int id: The id of the created organization.
    :>json list teams: The list of teams that the organization has.
    :>json list users: The list of users that are part of the organization.
    :status 200: When the organization is successfully generated.
    :status 400: When there is invalid information to update the organization.

    **Example request**:

    .. sourcecode:: http

       PUT /organizations/4 HTTP/1.1
       Content-Type: application/json

       {"name": "Brotherhood Without Banners"}

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {"name":"Brotherhood Without Banners","id":4,"teams":[],"url":"https://example.org/organizations/4","users":[]}

.. http:delete:: /organizations/(int:organization_id)

    Remove an existing organization.

    :status 204: Resource successfully deleted

   **Example request**:

   .. sourcecode:: http

      DELETE /organizations/4 HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content

.. http:post:: /organizations/(int:organization_id)/users/

    Add a user to an existing organization.

    :<json int user_id: The ID of the user to add.

    :status 204: User was successfully added.

    **Example request**:

    .. sourcecode:: http

        POST /organizations/4/users/ HTTP/1.1
        Content-Type: application/json

        {"user_id": 2}

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 204 No Content

.. http:delete:: /organizations/(int:organization_id)/users/(int:user_id)

    Remove a user from an organization.

    :status 204: User was successfully removed from an organization

    **Example request**:

    .. sourcecode:: http

        DELETE /organizations/4/users/2 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 204 No Content

Teams
^^^^^

.. http:get:: /teams/

    Get a list of all the teams you have read access to.

    **Example request**:

    .. sourcecode:: http

        GET /teams/ HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
            {
                "id": 4,
                "name": "admins",
                "permissions": [],
                "url": "https://example.org/teams/4",
                "organization": 7
            }
        ]

.. http:get:: /teams/

    Allows filtering of teams to retreive a subset.

    :query string type_contains:
        The type field on one of the resulting team's permissions must contain
        this string.
    :query string object_id:
        All the object_id fields on one of the resulting team's permissions
        must equal this string.

    **Example request**:

    .. sourcecode:: http

        GET /teams/?permission_contains=org&object_id=3 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "id": 4,
                "name": "organization admins",
                "permissions":
                    [
                        {
                            "id": 2,
                            "permission": "org:admins",
                            "object_id": "3"
                        }
                    ],
                "url": "https://example.org/teams/4",
                "organization": 3
            },
            {
                "id": 7,
                "name": "organization editors",
                "permissions":
                    [
                        {
                            "id": 3,
                            "permission": "org:write",
                            "object_id": "3"
                        }
                    ],
                "url": "https://exmple.org/teams/6",
                "organization": 3
        ]


.. http:post:: /teams/

    Create a new team.

    :<json str name: The name of the team.
    :<json int organization: The id of the organization that the team belongs to.

    :>json int id: The ID of the created team.
    :>json str url: The URL of the created team.
    :>json str name: the name of the team.
    :>json int organization: The id of the organization that the team belongs to.
    :>json list permissions:
        The permission list of the team. Each permission is an object
        containing the fields "id", "permission", and "object_id".
    :status 201: Successfully created team.
    :status 400: Missing required information to create team.

    **Example request**:

    .. sourcecode:: http

        POST /teams/ HTTP/1.1
        Content-Type: application/json

        {
            "name": "Lord Commanders",
            "organization": 7
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "id": 2,
            "name": "Lord Commanders",
            "permissions": [],
            "url": "https://example.org/teams/2",
            "organization": 7
        }

.. http:get:: /teams/(int:team_id)

    Get the details of a team.

    :>json int id: the ID of the team.
    :>json str url: the URL of the team.
    :>json str name: the name of the team.
    :>json int organization: The id of the organization that the team belongs to.
    :>json list permissions:
        The permission list of the team. Each permission is an object
        containing the fields "id", "permission", and "object_id".
    :status 200: Successfully retrieved team.

    **Example request**:

    .. sourcecode:: http

        GET /teams/2 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 2,
            "name": "Lord Commanders",
            "permissions": [],
            "url": "https://example.org/teams/2",
            "organization": 7
        }

.. http:put:: /teams/(int:team_id)

    Update the details of a team.

    :<json str name: The name of the team.

    :>json int id: the id of the updated team.
    :>json str url: The URL of the updated team.
    :>json str name: the name of the team.
    :>json int organization: The id of the organization that the team belongs to.
    :>json list permissions:
        The permission list of the team. Each permission is an object
        containing the fields "id", "permission", and "object_id".
    :status 200: successfully updated team.

    **Example request**:

    .. sourcecode:: http

        PUT /teams/2 HTTP/1.1
        Content-Type: application/json

        {
            "name": "Brotherhood without banners"
        }

    **Example reponse**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 2,
            "name": "Brotherhood without banners",
            "permissions": [],
            "url": "https://example.org/teams/2",
            "organization": 7
        }

.. http:delete:: /teams/(int:team_id)

    Remove a team.

    :status 204: Team successfully deleted.

    **Example request**:

    .. sourcecode:: http

        DELETE /teams/2 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 204 No Content

.. http:post:: /teams/(int:team_id)/permissions/

    Add a permission to a team.

    :<json str type: The string representing the permission.
    :<json str object_id:
        The id of the object that the permission acts on. "null" if it doesn't
        act on any object.
    :<json obj properties:
        A single layer object that can contain any amount of keys. Used to add
        additional information that might be useful to external applications.

    :>json int id: the id of the team.
    :>json str url: the URL of the team.
    :>json str name: the name of the team.
    :>json int organization: The id of the organization that the team belongs to.
    :>json list permissions:
        The permission list of the team. Each permission is an object
        containing the fields "id", "permission", and "object_id".
    :status 200: successfully added permission to the team.

    **Example request**:

    .. sourcecode:: http

        POST /teams/2/permissions/ HTTP/1.1
        Content-Type: application/json

        {
            "type": "org:admin",
            "object_id": "2",
            "properties": {}
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 2,
            "name": "Lord Commanders",
            "permissions": [
                {
                    "id": 17,
                    "type": "org:admin",
                    "object_id": "2",
                    "properties": {}
                }
            ],
            "url": "https://example.org/teams/2",
            "organization": 7
        }

.. http:delete:: /teams/(int:team_id)/permissions/(int:permission_id)

    Remove a permission from a team.

    :>json int id: the id of the team.
    :>json str url: The URL of the team.
    :>json str name: the name of the team.
    :>json int organization: The id of the organization that the team belongs to.
    :>json list permissions:
        The permission list of the team. Each permission is an object
        containing the fields "id", "permission", and "object_id".
    :status 200: successfully removed permission from the team.

    **Example request**:

    .. sourcecode:: http

        DELETE /teams/2/permissions/17 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 2,
            "name": "Lord Commanders",
            "permissions": [],
            "url": "https://example.org/teams/2",
            "organization": 7
        }

Users
^^^^^

.. http:get:: /users/

    Get a list of all users.

    **Example request**:

    .. sourcecode:: http

        GET /users/ HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "id": 1,
                "url": "https://example.org/users/1",
                "first_name": "Jon",
                "last_name": "Snow",
                "email": "jonsnow@castleblack.net",
                "admin": false,
                "teams": [
                    {
                        "id": 2,
                        "url": "https://example.org/teams/2"
                    }
                ],
                "organizations": [
                    {
                        "id": 4,
                        "url": "https://example.org/organizations/4"
                    }
                ]
            }
        ]

.. http:post:: /users/

    Create a new user.

    :<json str first_name: The (optional) first name of the user.
    :<json str last_name: The (optional) last name of the user.
    :<json str email: The email address of the user.
    :<json str password: The password for the user.
    :<json bool admin: True if the user is an admin user.

    :>json int id: The ID for the user.
    :>json str url: The URL for the user.
    :>json str first_name: The (optional) first name of the user.
    :>json str last_name: The (optional) last name of the user.
    :>json str email: The email address of the user.
    :>json bool admin: True if the user is an admin user.
    :>json list teams: A list of all the teams a user is a member of.
    :>json list organizations:
        A list of all the organizations the user is a member of.

    :status 201: Successfully created user.

    **Example request**:

    .. sourcecode:: http

        POST /users/ HTTP/1.1
        Content-Type: application/json

        {
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.net",
            "password": "gh0st",
            "admin": false
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "id": 1,
            "url": "https://example.org/users/1",
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.net",
            "admin": false,
            "teams": [],
            "organizations": []
        }

.. http:get:: /users/(int:user_id)

    Get details on a specific user.

    :>json int id: The ID for the user.
    :>json str url: The URL for the user.
    :>json str first_name: The (optional) first name of the user.
    :>json str last_name: The (optional) last name of the user.
    :>json str email: The email address of the user.
    :>json bool admin: True if the user is an admin user.
    :>json list teams: A list of all the teams a user is a member of.
    :>json list organizations:
        A list of all the organizations the user is a member of.

    **Example request**:

    .. sourcecode:: http

        GET /users/1 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 1,
            "url": "https://example.org/users/1",
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.net",
            "admin": false,
            "teams": [
                {
                    "id": 2,
                    "url": "https://example.org/teams/2"
                }
            ],
            "organizations": [
                {
                    "id": 4,
                    "url": "https://example.org/organizations/4"
                }
            ]
        }

.. http:put:: /users/(int:user_id)

    Update the information of an existing user. Cannot update the password this
    way, see the "Password resets" section on how to update the user password.

    :<json str first_name: The (optional) first name of the user.
    :<json str last_name: The (optional) last name of the user.
    :<json str email: The email address of the user.
    :<json bool admin: True if the user is an admin user.

    :>json int id: The ID for the user.
    :>json str url: The URL for the user.
    :>json str first_name: The (optional) first name of the user.
    :>json str last_name: The (optional) last name of the user.
    :>json str email: The email address of the user.
    :>json bool admin: True if the user is an admin user.
    :>json list teams: A list of all the teams a user is a member of.
    :>json list organizations:
        A list of all the organizations the user is a member of.

    :status 200: Successfully updated user.

    **Example request**:

    .. sourcecode:: http

        PUT /users/1 HTTP/1.1
        Content-Type: application/json

        {
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.org",
            "admin": true
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "id": 1,
            "url": "https://example.org/users/1",
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.org",
            "admin": true,
            "teams": [],
            "organizations": []
        }

.. http:delete:: /users/(int:user_id)

    Remove an existing user.

    :status 204: Successfully deleted the user.

    **Example request**:

    .. sourcecode:: http

        DELETE /users/1 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 204 No Content

.. http:post:: /users/(int:user_id)/teams/

    Place a user in a team

    :<json int team_id: The ID of the team to place the user in

    :>json int id: The ID for the user.
    :>json str url: The URL for the user.
    :>json str first_name: The (optional) first name of the user.
    :>json str last_name: The (optional) last name of the user.
    :>json str email: The email address of the user.
    :>json bool admin: True if the user is an admin user.
    :>json list teams: A list of all the teams a user is a member of.
    :>json list organizations:
        A list of all the organizations the user is a member of.

    :status 200: Successfully added the user to the team.

    **Example request**:

    .. sourcecode:: http

        POST /users/1/teams/ HTTP/1.1
        Content-Type: application/json

        {
            "team_id": 2
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 1,
            "url": "https://example.org/users/1",
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.net",
            "admin": false,
            "teams": [
                {
                    "id": 2,
                    "url": "https://example.org/teams/2"
                }
            ],
            "organizations": []
        }

.. http:delete:: /users/(int:user_id)/teams/(int:team_id)

    Remove the user from the specified team.

    :>json int id: The ID for the user.
    :>json str url: The URL for the user.
    :>json str first_name: The (optional) first name of the user.
    :>json str last_name: The (optional) last name of the user.
    :>json str email: The email address of the user.
    :>json bool admin: True if the user is an admin user.
    :>json list teams: A list of all the teams a user is a member of.
    :>json list organizations:
        A list of all the organizations the user is a member of.

    :status 200: Successfully removed the user from the team.

    **Example request**:

    .. sourcecode:: http

        DELETE /users/1/teams/2 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": 1,
            "url": "https://example.org/users/1",
            "first_name": "Jon",
            "last_name": "Snow",
            "email": "jonsnow@castleblack.net",
            "admin": false,
            "teams": [],
            "organizations": []
        }
