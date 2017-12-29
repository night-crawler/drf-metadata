from django.http import HttpRequest
from rest_framework.views import APIView

from drf_metadata.meta import MetaData, AbstractField, CustomMetadata
from pytests.test_app.models import Author, Book, Publisher
from pytests.utils import force_evaluate, get_field_by_name, NoneSerializer


def prepare_dataset():
    Publisher.objects.all().delete()
    Author.objects.all().delete()
    Book.objects.all().delete()

    publishers = [Publisher.objects.create(name='pub%s' % i) for i in range(3)]
    authors = [Author.objects.create(name='author%s' % i, birth='1950-02-02') for i in range(3)]

    b1 = Book.objects.create(
        title='book1',
        publisher=publishers[0],
    )
    b1.authors.set(authors[:2])
    b1.save()


prepare_dataset()


class MyAPIView(APIView):
    def get_view_description(self, html=False):
        return 'description'


class AuthorMetaData(MetaData):
    model = Author


class BookMetaData(MetaData):
    model = Book


class PublisherMetaData(MetaData):
    model = Publisher


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


# noinspection PyMethodMayBeStatic
class MetaDataTest:
    def test__determine_metadata_plain(self):
        _metadata = AuthorMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert metadata == {
            'title': 'author',
            'description': 'description',
            'fields': [
                {
                    'type': 'CharField',
                    'name': 'name', 'verbose_name': 'name', 'help_text': '',
                    'blank': False, 'null': False, 'editable': True, 'max_length': 255, 'required': True
                },
                {
                    'type': 'DateField',
                    'name': 'birth', 'verbose_name': 'birth date', 'help_text': '',
                    'blank': False, 'null': False, 'editable': True, 'required': True
                }
            ]
        }

    def test__title(self):
        class CustomBookMetaData(BookMetaData):
            def get_title(self, request, view, obj):
                return 'my title'

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)
        assert metadata['title'] == 'my title'

    def test__model_with_relations(self):
        """
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
        """

        _metadata = BookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert [data['name']
                for data in get_field_by_name(metadata, 'publisher')['data']] == ['pub0', 'pub1', 'pub2']
        assert [data['name']
                for data in get_field_by_name(metadata, 'authors')['data']] == ['author0', 'author1', 'author2']

    def test_choices(self):
        _metadata = PublisherMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)
        assert get_field_by_name(metadata, 'state')['choices'] == [[0, 'Active'], [1, 'Disabled']]

    # noinspection PyPep8Naming
    def test__get_NAME_queryset(self):
        # noinspection PyMethodMayBeStatic
        class CustomBookMetaData(BookMetaData):
            def get_authors_queryset(self, field):
                return Author.objects.filter(name='author0')

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert [data['name'] for data in get_field_by_name(metadata, 'authors')['data']] == ['author0']

    def test__static_serializers(self):
        # noinspection PyMethodMayBeStatic
        class CustomBookMetaData(BookMetaData):
            serializers = {
                'publisher': NoneSerializer
            }

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert get_field_by_name(metadata, 'publisher')['data'] == [{}, {}, {}]

    # noinspection PyPep8Naming
    def test__get_NAME_serializer(self):
        # noinspection PyMethodMayBeStatic
        class CustomBookMetaData(BookMetaData):
            def get_authors_serializer(self, field):
                return NoneSerializer

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert metadata['fields'][2]['data'] == [{}, {}, {}]

    # noinspection PyPep8Naming
    def test__get_NAME_dataset_url(self):
        # noinspection PyMethodMayBeStatic
        class CustomBookMetaData(BookMetaData):
            def get_publisher_dataset_url(self, field, obj):
                return 'publisher_url'

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert get_field_by_name(metadata, 'publisher')['data'] == 'publisher_url'

    def test__dataset_urls(self):
        class CustomBookMetaData(BookMetaData):
            dataset_urls = {
                'authors': '/author/',
                'publisher': '/publisher/',
            }

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert get_field_by_name(metadata, 'authors')['data'] == '/author/'
        assert get_field_by_name(metadata, 'publisher')['data'] == '/publisher/'

    def test__update_fields(self):
        class CustomBookMetaData(BookMetaData):
            update_fields = {
                'authors': {
                    'omg': {'lol': 1}
                }
            }

        _metadata = CustomBookMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)
        assert get_field_by_name(metadata, 'authors')['omg'] == {'lol': 1}


# noinspection PyMethodMayBeStatic
class AbstractFieldTest:
    def test_field(self):
        field_data = AbstractField(
            type='ForeignKey',
            name='user_id',
            verbose_name='User',
            formatter='user',
            data='/data',
            required=True)
        assert field_data == {
            'type': 'ForeignKey',
            'name': 'user_id', 'verbose_name': 'User', 'help_text': '',
            'blank': True, 'null': False, 'required': True,
            'formatter': 'user', 'data': '/data',
        }


# noinspection PyMethodMayBeStatic
class CustomMetaDataTest:
    def test_init(self):
        _metadata = ImpersonateMetadata().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert metadata == {
            'title': 'View site as another user',
            'action_name': 'Impersonate',
            'description': 'description',
            'fields': [
                {
                    'data': '/data/',
                    'name': 'user_id',
                    'verbose_name': 'User',
                    'required': True, 'help_text': '',
                    'blank': True,
                    'null': False,
                    'type': 'ForeignKey'
                }
            ]
        }

    # noinspection PyPep8Naming
    def test__get_NAME(self):
        # noinspection PyMethodMayBeStatic
        class MethodMetadata(CustomMetadata):
            title = 'title'
            action_name = 'action'

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

        _metadata = MethodMetadata().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert metadata == {
            'title': 'title',
            'action_name': 'action',
            'description': 'description',
            'fields': [
                {'name': 'hero', 'super': True},
                {'name': 'lol', 'super': False},
            ]
        }

    # noinspection PyPep8Naming
    def test__get_field_NAME(self):
        class CustomImpersonateMetadata(ImpersonateMetadata):
            def get_field_user_id(self, field_name, request):
                return {
                    'lol': 1
                }

        _metadata = CustomImpersonateMetadata().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)
        assert metadata == {
            'title': 'View site as another user', 'action_name': 'Impersonate', 'description': 'description',
            'fields': [
                {
                    'type': 'ForeignKey', 'name': 'user_id', 'verbose_name': 'User',
                    'required': True, 'blank': True, 'null': False, 'help_text': '',
                    'data': '/data/',
                    'lol': 1
                }
            ]
        }
