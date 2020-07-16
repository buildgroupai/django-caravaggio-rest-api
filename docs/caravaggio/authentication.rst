.. _caravaggio_authentication:

.. highlight:: rst

.. role:: python(code)
    :language: python

.. role:: latex(code)
    :language: latex

==============
Authentication
==============

All access to Caravaggio API needs to be authenticated. Authentication is performed in two ways:

- by including in the ``Authorization`` HTTP header. The key should be prefixed by the string literal "Token", with whitespace separating the two strings. For example:

    .. code-block:: shell

        export CARAVAGGIO_TOKEN=1b90d33bd716bc4aee91f6750d6aaf3a5ab6e19b
        curl -H 'Authorization: Token '${CARAVAGGIO_TOKEN}'' \
            "http://localhost:8001/users/user/"


- **Not recommended** by appending your auth_token to the query string of every request. Click the link below to see an example of an authenticated API request which will list the users.

    .. code-block:: shell

        https://localhost:8001/users/user?auth_token=1b90d33bd716bc4aee91f6750d6aaf3a5ab6e19b

Your **TOKEN** is a unique identifier that is assigned exclusively to your account. Remember to keep your **TOKEN** secret.

To use Caravaggio from the command line, we recommend setting your **TOKEN** as environment variable. Using environment variables is also an easy way to keep your **TOKEN** out of your source code.

Copy and paste the snippet below in your terminal to make CARAVAGGIO_TOKEN ready to use.

.. code-block:: shell
   :linenos:
   :emphasize-lines: 3,5

    export CARAVAGGIO_TOKEN=1b90d33bd716bc4aee91f6750d6aaf3a5ab6e19b


$ Setting user's Authentication Parameters If you are a Windows command line user, use the following snippet instead:

.. code-block:: shell
   :linenos:

    set CARAVAGGIO_TOKEN=1b90d33bd716bc4aee91f6750d6aaf3a5ab6e19b


$ Setting user's Authentication Parameters in Windows
Here is an example of an authenticated API request to list the users from a command line.

.. code-block:: shell
   :linenos:

   curl -H 'Authorization: Token '${CARAVAGGIO_TOKEN}'' \
        "http://localhost:8001/users/user/"

This is the kind of expected response:

.. code-block:: json

    {
       "count":2,
       "next":null,
       "previous":null,
       "results":[
          {
             "id":"04771934-d974-4fe6-bf53-560816e056cb",
             "client":"62df90ca-ca50-4bb8-aab7-a2159409cf67",
             "email":"xalperte+2@builgroupai.com",
             "first_name":"Javier 2",
             "last_name":"Alperte 2",
             "is_staff":false,
             "is_client_staff":false,
             "date_joined":"2019-09-20T14:55:11.063098Z"
          },
          {
             "id":"ade7efa4-1ba7-48bb-8d2a-bc893954ca4f",
             "client":"62df90ca-ca50-4bb8-aab7-a2159409cf67",
             "email":"xalperte@buildgroupai.com",
             "first_name":"Javier",
             "last_name":"Alperte",
             "is_staff":true,
             "is_client_staff":true,
             "date_joined":"2019-09-17T09:25:06.420406Z"
          }
       ]
    }


****************
Alternative Keys
****************

Alternative Keys allow you to give fine-grained access to your resources.
To create an alternative key you need to use the web interface. There you can define what resources an alternative key can access and what operations (i.e., create, list, retrieve, update or delete) are allowed with it. This is useful in scenarios where you want to grant different roles and privileges to different applications. For example, an application for the IT folks that collects data and creates new resources, another that is accessed by data scientists to get and evaluate available data, and a third that is used by the investment analysts folks to manage their deal-flow.

You can read more about alternative keys here.
