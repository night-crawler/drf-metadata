import django

import typing as t
from collections import OrderedDict, namedtuple

from django.db import models
from django.http.request import HttpRequest
from django.utils.encoding import force_text
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

DRFMimicSerializer = namedtuple('DRFMimicSerializer', ['data'])
DRFSerializerOrMimicSerializerType = t.Type[t.Union[Serializer, t.Callable[DRFMimicSerializer]]]


class MetaData:
    URL_PK_PLACEHOLDER = 'object_pk'

    model: t.Union[models.Model, None] = None
    request: t.Union[HttpRequest, None] = None
    fields: t.List[str] = []
    attr_list = [
        'name', 'verbose_name', 'help_text',
        'blank', 'null',
        'editable',
        'max_length',
        # 'auto_created', 'is_relation', 'hidden', 'concrete',
    ]

    update_fields = {}

    exclude: t.List[str] = []
    include_hidden = False
    include_parents = True
    concrete_in = [True]
    auto_created_in = [False]
    editable_in = [True]

    serializers: t.Dict[str, DRFSerializerOrMimicSerializerType] = {}
    dataset_urls = {}
    no_data = []

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def get_NAME_serializer(self, field, qs) -> Serializer:
        """
        Returns serializer <NAME> field. This method (`get_NAME_serializer`) is not supposed to use directly.
        :param field:
        :param qs:
        :return: Serializer
        """
        raise Exception()

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def get_NAME_queryset(self, field) -> models.QuerySet:
        """
        Redefines field <NAME> queryset (fk, m2m, etc. querysets).
            This method (`get_NAME_queryset`) is not supposed to use directly.
        :param field:
        :return: QuerySet()
        """
        raise Exception()

    # noinspection PyProtectedMember
    def get_field_related_model(self, field_name: str) -> models.Model:
        return self.model._meta.get_field(field_name).related_model

    @staticmethod
    def format_choices(field: models.Field):
        for choice in field.choices:
            printable_name = force_text(choice[1])
            yield [choice[0], printable_name]

    @staticmethod
    def is_required(field: models.Field) -> bool:
        if field.editable is False:
            return False
        if field.auto_created is True:
            return False
        if field.hidden is True:
            return False

        blank = getattr(field, 'blank', None)
        if blank is True:
            return False
        if blank is False:
            return True

        return True

    # noinspection PyUnusedLocal
    @staticmethod
    def default_queryset_serializer(qs: models.QuerySet, many: bool = False) -> DRFMimicSerializer:
        """
        Simple serializer that looks like default DRF serializer
        :param qs: queryset
        :param many: not used, mimic to DRF serializer
        :return:
        """
        res = [{'id': item.id, 'name': str(item)} for item in qs]
        return DRFMimicSerializer(data=res)

    def get_serializer(self, field: models.Field) -> DRFSerializerOrMimicSerializerType:
        # try to find serializer in MetaData instance first
        get_serializer_method = getattr(self, 'get_%s_serializer' % field.name, None)
        if callable(get_serializer_method):
            return get_serializer_method(field)

        # next check serializer dictionary in self.serializers
        serializer = self.serializers.get(field.name, None)
        if serializer is not None:
            return serializer

        # if no appropriate serializers were found use default drf-mimic serializer
        return self.default_queryset_serializer

    def serialize_queryset(self, field: models.Field, qs: models.QuerySet) -> t.Dict:
        serializer = self.get_serializer(field)
        return serializer(qs, many=True).data

    def get_field_related_data(self, field):
        qs = self.get_field_queryset(field)
        return self.serialize_queryset(field, qs)

    # noinspection PyProtectedMember
    def get_meta(self) -> t.Generator[t.Dict, None, None]:
        all_fields = self.model._meta.get_fields(
            include_parents=self.include_parents, include_hidden=self.include_hidden
        )
        for f in all_fields:
            if f.name in self.exclude:
                continue
            if self.fields and f.name not in self.fields:
                continue

            if f.name not in self.fields:
                if f.concrete not in self.concrete_in:
                    continue
                if f.auto_created not in self.auto_created_in:
                    continue
                if f.editable not in self.editable_in:
                    continue

            yield self.get_field_meta(f)

    def get_field_queryset(self, field: models.Field) -> models.QuerySet:
        custom_queryset_method = getattr(self, 'get_%s_queryset' % field.name.lower(), None)
        if custom_queryset_method is not None:
            return custom_queryset_method(field)

        model = self.get_field_related_model(field.name)
        return model.objects.all()

    def get_field_meta(self, field: models.Field) -> OrderedDict:
        d = OrderedDict()
        sentinel = object()

        for attr in self.attr_list:
            val = getattr(field, attr, sentinel)
            if val is sentinel:
                continue
            if attr in ['max_length']:
                if val is None:
                    continue

            if attr in ['verbose_name']:
                val = force_text(val)

            d[attr] = val

        d['type'] = field.get_internal_type()
        d['required'] = self.is_required(field)
        if field.default != models.NOT_PROVIDED:
            d['default'] = field.default
        if hasattr(field, 'choices') and field.choices:
            d['choices'] = list(self.format_choices(field))

        if field.related_model:
            if field.name not in self.no_data:
                if field.name in self.dataset_urls:
                    d['data'] = force_text(self.dataset_urls[field.name])
                else:
                    d['data'] = self.get_field_related_data(field)

        data_update = self.update_fields.get(field.name, {})
        d.update(data_update)

        return d

    def determine_metadata(self, request: HttpRequest, view: APIView):
        self.request = request

        if isinstance(self.model, str):
            self.model = django.apps.apps.get_model(*self.model.split('.'))

        # noinspection PyProtectedMember
        return {
            'title': self.model._meta.verbose_name,
            'description': view.get_view_description(),
            'fields': self.get_meta(),
        }


class AbstractField(dict):
    def __init__(self,
                 type: str = '', name: str = '', verbose_name: str = '',
                 blank: bool = True, required: bool = False, help_text: str = '', null: bool = False,
                 update_callable: bool = False, **kwargs):
        """
        :param type: str, field type e.g 'MultipleChoiceField'
        :param name: str, field name
        :param verbose_name: str or ugettext_lazy
        :param blank: similar to django blank
        :param required: similar to django required
        :param help_text: similar to django help_text
        :param null: similar to django null
        :param kwargs: dict, add pairs to result AbstractField dict
        field = AbstractField(type='MultipleChoiceField', name='translation_formats',
                              verbose_name=_('Translation formats'), choices=models.Resource.EXPORT_CHOICES)
        """
        super().__init__(**kwargs)
        assert name, 'No element name provided'
        assert verbose_name, 'No element verbose name provided'
        assert type, 'No element type name provided'

        self.update_callable = update_callable
        self.update({
            'name': name,
            'verbose_name': verbose_name,
            'required': required,
            'help_text': help_text,
            'blank': blank,
            'null': null,
            'type': type,
        })
        for k, v in kwargs.items():
            self[k] = v


class CustomMetadata:
    """
    Metadata class for non-model forms
    """
    fields = []
    order = []
    request = None
    title = None
    action_name = None

    def get_meta(self, obj=None) -> t.Generator[t.Dict, None, None]:
        """
        :return: generator
        list(metadata_obj.get_meta()) -> [abstract_field_obj1, abstract_field_obj2, ...]
        """
        fields_by_name = OrderedDict()
        for field_data in self.fields:
            fields_by_name[field_data['name']] = field_data

        for k, v_callable in self.__class__.__dict__.items():
            # method `get_field_<NAME>` used for updates later
            if k.startswith('get_field_'):  # get_field_ обновляет существующее поле
                continue
            if not k.startswith('get_'):
                continue
            # check dynamic get_%s fields
            # методы get_%s должны возвращать {'name': 'qwe'}
            res = v_callable(self, self.request)
            fields_by_name[res['name']] = res

        fields_order = self.order or fields_by_name.keys()

        for field_name in fields_order:
            field_value = fields_by_name[field_name]
            # метод должен вернуть dict, которым будет обновлено поле
            method = getattr(self, 'get_field_%s' % field_name, None)
            if callable(method):
                field_value.update(method(field_name, self.request))

            yield field_value

    def determine_metadata(self, request, obj=None) -> t.Dict:
        """
        Returns metadata dict with fields and names
        :param request: object of HTTP request
        :param obj: view instance object
        :return: dict
        metadata_obj.determine_metadata(request, view_obj) -> {
            'title': 'Get some privileges',
            'description': 'Become a member of fsociety',
            'action_name': 'OK',
            'fields': generator
        }
        """
        self.request = request
        return {
            'title': self.title or '',
            'action_name': self.action_name or 'OK',
            'fields': self.get_meta(obj),
        }
