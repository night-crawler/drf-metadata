Installation
------------
.. code:: bash

    pip install -e git+https://github.com/night-crawler/drf-metadata.git@#egg=drf-metadata

Models
------

.. code:: python

    class Author(models.Model):
        name = models.CharField(max_length=255)
        birth = models.DateField('birth date')

        def __str__(self):
            return self.name


    class Publisher(models.Model):
        name = models.CharField(max_length=255)
        state = models.PositiveSmallIntegerField(
            'publisher state',
            choices=(
                (0, 'Active'),
                (1, 'Disabled')
            ),
            default=1
        )

        def __str__(self):
            return self.name


    class Book(models.Model):
        title = models.CharField(max_length=255)
        authors = models.ManyToManyField(Author)
        publisher = models.ForeignKey(Publisher)

Usage
-----

.. code:: python

    from drf_metadata.meta import MetaData, AbstractField, CustomMetadata

    class BookMetadata(MetaData):
        model = Book

        serializers = {
            'publisher': PublisherSerializer
        }

        update_fields = {
            'authors': {
                'omg': {'lol': 1}
            }
        }

        # skip serialization
        dataset_urls = {
            'authors': '/author/',
            'publisher': '/publisher/',
        }

        def get_authors_queryset(self, field):
            return Author.objects.filter(name='author0')

        def get_authors_serializer(self, field):
            # self.request, self.view, self.obj are available in MetaData instance
            return AuthorSerializer

Usage with django-rest-framework
--------------------------------

.. code:: python

    # or redefine OPTIONS handler
    class BookViewSet(viewsets.ReadOnlyModelViewSet):
        @list_route()
        def describe_book(self, request):
            md = metadata.BookMetadata().determine_metadata(request, self)
            return Response(md)

Sample response
---------------

.. code:: json

    {
        'title': 'book', 'description': 'description',
        'fields': [
            {
                'type': 'CharField', 'max_length': 255,
                'name': 'title',
                'verbose_name': 'title',
                'help_text': '', 'blank': False, 'null': False, 'editable': True, 'required': True},
            {
                'type': 'ForeignKey',
                'name': 'publisher', 'verbose_name': 'publisher', 'help_text': '',
                'blank': False, 'null': False, 'editable': True, 'required': True,
                'data': [
                    {'id': 47, 'name': 'pub0'},
                    {'id': 48, 'name': 'pub1'},
                    {'id': 49, 'name': 'pub2'}
                ]
            },
            {
                'type': 'ManyToManyField',
                'name': 'authors', 'verbose_name': 'authors', 'help_text': '',
                'blank': False, 'null': False, 'editable': True, 'required': True,
                'data': [
                    {'id': 37, 'name': 'author0'},
                    {'id': 38, 'name': 'author1'},
                    {'id': 39, 'name': 'author2'}
                ]
            }
        ]
    }

Non-model MetaData
------------------

.. code:: python

    class ImpersonateMetadata(CustomMetadata):
        title = 'View site as another user'
        action_name = 'Impersonate'

        fields = (
            AbstractField(type='ForeignKey',
                          name='user_id',
                          verbose_name='User',
                          data='/data/',
                          required=True),
        )

        # method fields
        def get_superfield(self, request):
            return {
                'name': 'hero',
                'super': True
            }

        def get_lol(self, request):
            return {
                'name': 'lol',
                'super': False
            }

        # update field `user_id`
        def get_field_user_id(self, field_name, request):
            return {
                'lol': 1
            }