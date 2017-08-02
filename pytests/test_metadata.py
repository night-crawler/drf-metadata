import json
from pprint import pprint

from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from drf_metadata.meta import MetaData
from pytests.test_app.models import Author, Book, Publisher


# noinspection PyAbstractClass
class NoneSerializer(serializers.Serializer):
    pass


def force_evaluate(val):
    s = JSONRenderer().render(val)
    return json.loads(s)


def get_field_by_name(bundle: dict, field_name: str):
    for field_data in bundle['fields']:
        if field_data['name'] == field_name:
            return field_data
    return None


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
    b1.authors = authors[:2]
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


class AbstractFieldTest:
    pass