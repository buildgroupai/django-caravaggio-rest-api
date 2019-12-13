##########
Changelog
##########

Current 0.1.7
=============

New Features
************

- Development, Staging and Production settings with `django-configurations <https://django-configurations.readthedocs.org>`_.


- Support for mixed ORMs in the same project: Django Models + DSE models. We have implemented some things to make possible the use of both DSE and Django models in the same application.


- Users subsystem for support for Client (External System), Organizations, and Users

    - It's plugable, if we need to implement a API that wants to use the normal Django model, we only need to comment some settings in the settings.py.

    - Implemented using normal Django Models.

    - :class:`caravaggio_rest_api.users.models.CaravaggioClient`. Represents external systems. It's a way any other client could use our platform to create its own application and manage its own users. Only the **superuser** can create *Clients*. We can create users that are administrators of the Client instance, allowing the creation of organizations/users inside the Client space.

    - :class:`caravaggio_rest_api.users.models.CaravaggioOrganization`.  A way to group users. The organization has an Owner (user), and also could have different collections of users: *administrators*, *members*, and *restricted members*.


- Define GDAL dependencies as extras. Now we only install them if our model is going to use spatial searches.

    .. code-block:: shell

        pip install -e django-caravaggio-rest-api[spatial]


- A new django app **caravaggio_rest_api.logging** used to log in C* all the access that are made to the API.

    - We control the persistence behaviour of the events through ``settings.REST_FRAMEWORK.LOG_ACCESSES``.

- Add `drf-yasg <https://github.com/axnsan12/drf-yasg>`_ to allow OpenAPI endpoints (schema, documentation)

   - Swagger doc: http://localhost:8001/swagger/
   - ReDoc doc: http://localhost:8001/redoc/

- Support for project documentation using Sphinx.

    .. code-block:: shell

        python setup.py docs


- Define a Test base class to assist on the implementation of complex tests composed by a set of ordered steps that has to be executed atomically.

.. code-block:: python
   :linenos:

    class GetAllClientTest(CaravaggioBaseTest):

        @classmethod
        def setUpTestData(cls):
            super().setUpTestData()
            blah blah

        def step1_create_clients(self):
            blah blah

        def step2_get_clients(self):
            blah blah

        def step3_search_name(self):
            blah blah


- Add support for DRF filter to allow complex queries when using Django Models. This is the case of the users subsystem (Client, Organization, User)


- Add support for search on Tuple/UDF fields. These ara the kind of queries sent to Solr: ``q={!tuple v='address.street_type:(Street)'}``. As a user, we will be able to inform these filters like this: ``/?address_street_type=Street`` or any of its variants ``/?address_street_type__icontains=Street``.

    .. note::

        Facets are not supported for the members of Tuple/UDF fields.


.. code-block:: python
   :linenos:

	# Our Tuple/UDF model (Address)
	class Address(UserType):
	    """
	    A User Defined type for model an Address, a unit value to be consolidated
	    """
	    __type_name__ = "address"

	    street_type = columns.Text()
	    street_name = columns.Text()
	    ...

	# Our main model class with a reference to the UDF class (Company)
	class Company(CustomDjangoCassandraModel):
	    """
	    A public traded company
	    """
	    __table_name__ = "company"

	    # A unique identifier of the entity
	    _id = columns.UUID(partition_key=True, default=uuid.uuid4)


	    # The name of the company
	    name = columns.Text(required=True)

	    ...

	    # Address of the headquarters of the company
	    address = UserDefinedType(Address)
		...


	# Now we can define the search index
	class CompanyIndex(BaseSearchIndex, indexes.Indexable):

	    _id = indexes.CharField(
	        model_attr="_id")

	    name = indexes.CharField(
	        model_attr="name")

	    ...

        # Address UDT fields
	    address_street_type = indexes.CharField(
	        model_attr="address.street_type")
	    address_street_name = indexes.CharField(
	        model_attr="address.street_name")
	    address_street_number = \
	        indexes.IntegerField(model_attr="address.street_number")
	    address_state = indexes.CharField(
	        model_attr="address.state", faceted=True)
	    address_region = indexes.CharField(
	        model_attr="address.region", faceted=True)
	    address_city = indexes.CharField(
	        model_attr="address.city", faceted=True)
	    address_country_code = indexes.CharField(
	        model_attr="address.country_code", faceted=True)
	    address_zipcode = indexes.CharField(
	        model_attr="address.zipcode", faceted=True)
	    ...

	# Now it's time to define the DRF Serializer class for the Address class (UDT/Tuple)
	class AddressSerializer(dse_serializers.UserTypeSerializer):

	    street_type = serializers.CharField(required=False, max_length=10)
    	street_name = serializers.CharField(required=False, max_length=150)
    	...

	# And the main Company serializer class
	class CompanySearchSerializerV1(CustomHaystackSerializer, BaseCachedSerializerMixin):

	    """
	    A Fast Searcher (Solr) version of the original Business Object API View
	    """
	    address = AddressSerializer()
	    ...

	    score = fields.FloatField(required=False)
	    ...

	    class Meta(CustomHaystackSerializer.Meta):
	        model = Company

	        index_classes = [CompanyIndex]

	        fields = [
	            "_id",
	            "name", ...,
	            "address_street_type", "address_street_name",
	            ...,
	            "text", "score"
	        ]

    # And the last piece, the ViewSet that process the user requests to the API.

	class CompanySearchViewSet(CaravaggioHaystackFacetSearchViewSet):

	    index_models = [Company]

	    serializer_class = CompanySearchSerializer

	    results_serializer_class = CompanySerializer

	    ordering_fields = ("_id",
	                       "created_at", "updated_at", "foundation_date",
	                       "country_code", "stock_symbol")


- A custom Router to have a better control of the operations available per `ViewSet`:

.. code-block:: python
   :linenos:

   from django.conf import settings
   from django.conf.urls import url, include

   from caravaggio_rest_api.example.company.api.views import CompanyViewSet, CompanySearchViewSet, CompanyGEOSearchViewSet
   from caravaggio_rest_api.drf.routers import CaravaggioRouter

   # API v1 Router. Provide an easy way of automatically determining the URL conf.

   api_SEARCH_COMPANY = CaravaggioRouter(actions=["list"])

   if settings.DSE_SUPPORT:
       api_SEARCH_COMPANY.register(
           r'company/search',
           CompanySearchViewSet,
           base_name="company-search")

       api_SEARCH_COMPANY.register(
           r'company/geosearch',
           CompanyGEOSearchViewSet,
           base_name="company-geosearch")

   api_COMPANY = CaravaggioRouter()

   api_COMPANY.register(r'company',
                        CompanyViewSet, base_name="company")

   urlpatterns = [
       # Company API version
       url(r'^',
           include(api_SEARCH_COMPANY.urls + api_COMPANY.urls),
           name="company-api"),
   ]


- A custom exception handler has been added to DRF to add more information to the error message the platform is sending to the client. The handler has been defined in `caravaggio_rest_api.drf.exceptions.caravaggio_exception_handler`. This handler
adds the following details to the response:

    - `status`: this ensures that all error responses include the HTTP status code in the body of the response.

    The handler has been registered in `settings.py` as follows:

.. code-block:: python
   :linenos:

   REST_FRAMEWORK = {
       'EXCEPTION_HANDLER':
            'caravaggio_rest_api.drf.exceptions.caravaggio_exception_handler'
   }

- Ability to overwrite the throttling rates configuration per view declaring a field called `throttle_operations`. Example:

.. code-block:: python
   :linenos:

   class CompanySnapshotSearchViewSet(CaravaggioHaystackFacetSearchViewSet):

   throttle_operations = {
      'list': '10/minute'
   }

- Ability to configure the facets on the request using `facet.field.<FIELD_NAME>` parameters. Ex.

.. code-block:: shell

   URL="http://localhost:8002/companies/company-snapshot/search/facets/?"
   URL=$URL"facet.field.headcount=start:0,end:500,gap:20"
   URL=$URL"&facet.field.foundation_date=start_date:2000-01-01,end_date:2019-11-25,gap_by:year,gap_amount:1"
   URL=$URL"&limit=1"
   curl -X GET $URL \
       -H "Content-Type: application/json" \
       -H "Authorization: Token ${CARAVAGGIO_TOKEN}"

- Ability to combine filters and facets to restrict the faceting operation to a subset of documents. Ex.

.. code-block:: shell

   URL="http://localhost:8002/companies/company-snapshot/search/facets/?"
   URL=$URL"facet.field.headcount=start:0,end:500,gap:20"
   URL=$URL"&facet.field.foundation_date=start_date:2000-01-01,end_date:2019-11-25,gap_by:year,gap_amount:1"
   URL=$URL"&country_code__in=USA,CAN"
   URL=$URL"&status__in=running,zombie"
   URL=$URL"&foundation_date__gte=2000-01-01T00:00:00.0Z"
   URL=$URL"&funding_sum__gte=1000000"
   URL=$URL"&limit=1"
   curl -X GET $URL \
       -H "Content-Type: application/json" \
       -H "Authorization: Token ${CARAVAGGIO_TOKEN}"

Improvements or Changes
***********************

- Using `django-configurations` to manage the settings of different environments (dev, staging, production, etc.)

- Use of setup.cfg to put all the configuration of the project

- We have included the library code inside the `src` folder to avoid side effects

- Add support for Django-debug-toolbar and Django-extensions for debug

- Tests for Clients (External systems)


Bug Fixing
**********

- Fix bug when the results of a search query comes empty. We were accessing to some attributes that are not available when there is no results."
- Fix bug to serialize UserTypes, the bug occurs when we try to serialize a list of UserTypes or when we have a UserType inside of another UserType.



Version 0.1.6
=============

New Features
************

No new features

Improvements or Changes
***********************

No new features

Bug Fixing
**********

- Update version of Django Cassandra Engine to 1.5.5 that fixes issues creating the Test DB.
- The TestRunner implementation of setup_databases was not returning the old config making impossible the destroy of the test databases at the end of the tests.
- CaravaggioBaseTest must inform about to use all the databases in the test, if not, only the default database is used. Ex. databases = "\_\_al\_\_"




Version 0.1.5
=============

New Features
************

No new features

Improvements or Changes
***********************

- Now the code belongs to BGDS, we have updated the copyright headers to reflect it.
- Remove dependencies to preseries github repo and change it by buildgroupai.

Bug Fixing
**********

- Update version of DRF-Haystack to 1.8.5 and remove the reference to the DRF dependency from our setup.py. We will ue by default the DRF version declared in the DRF-Haystack project to avoid conflict in versions.
- Missing dependency with pyyaml needed by the OpenAPI
- Update GDAL library version to avoid compilation problems



Version 0.1.4
=============

New Features
************

- Support for "group" searches in Solr Backend, and pagination of user responses using *caravaggio_rest_api.haystack.backends.utils.CaravaggioSearchPaginator*.


Improvements or Changes
***********************

No improvements

Bug Fixing
**********

- Frozen the version of GDAL library to avoid deployment/compilation problems.




Version 0.1.3
=============

New Features
************

- Added support for `regex` queries in text fields. Ex. number__regex=1.01.(.*).01(.*)
   Example of request: `http://localhost:8001/bovespa/company-account/search/?period=2018-06-30T00:00:00Z&ccvm=15300&financial_info_type=INSTANT&number__iregex=1.01.(.*).01(.*)&order_by=number`

Improvements or Changes
***********************

- Refactoring of the haystack overrided classes. Now we have a package for them `haystack` and each class is in a file of the same name in the official Haystack, to make easiest the maintenance of the code.

Bug Fixing
**********

No bugs fixed


Version 0.1.2
=============

New Features
************

- Added a custom HaystackOrderingFilter to support indexed fields with `faceted=True`. We need to change the name of the field from `FIELD_NAME` to `FIELD_NAME_exact`.
- Added the parameter `COERCE_DECIMAL_TO_STRING: False` into the settings.py file, in the `REST_FRAMEWORK` config variable. This parameter force all the decimal numbers to be rendered as decimal numbers, not as strings, as it's its the behavior by default.

Improvements or Changes
***********************

- A new DSE `Decimal` column has been added to the framework. It's a simple version of the original columns.Decimal that defines two more arguments in the constructor: `max_digits` and `decimal_places`. Two fields needed by the DRF DecimalField serializer in order to serialize/deserialize at each request. The column do not use these new arguments internally.
- Refactoring of some files. A new `dse` and `drf_haystack` packages with all its artifacts have been added.
- The included example have been adapted to the new changes

Bug Fixing
**********

No bugs fixed



Version 0.1.1
=============

New Features
************

- A new DRF serializer field `CurrentUserNameDefault` added to allow inject the name of the current logged user as a default value.
- A new class `CaravaggioSearchPaginator` has been added to allow direct queries to **Solr** paginating the results using a native **Solr Cursor**.
- A new argument added to the `sync_indexes` management command (**--model**) to generate only the search index of the informed model class (full qualifier name is required, ex. `caravaggio_rest_api.example.models.Company`)
- Added a complete example of use of Caravaggio:
    - __a complete C* model__, with fields of type `UserType`, `Maps`, `Lists`, etc., and with `Django callbacks`.
    - __a complete search index__, with a declared field of type `LocationField` (named `coordinates`), with facets declared,  ranges declared for dates, indexing of lists and maps, and text field support for text search on all the textual fields.
    - __a REST endpoints__ for the API, one direct object access (C*) , a **Solr** search endpoint with facets supports, and a **Solr Spatial** Search endpoint with support for spatial searches.
     - __a complete Test Suite__ to test the previous code and to show how to test the code in a production project.
- Caravaggio is now fully functional. We added all the required files to run the application. We can start the server (runserver) and tests the library through the new added example.

Improvements or Changes
***********************

- Improved the method "load_test_data" in the base tests class `CaravaggioBaseTest`. Now we are injecting a fake request with the currently logged in user set (ApiClient) to allow the proper operation of the serializer field `CurrentUserNameDefault`.

Bug Fixing
**********

No bugs fixed