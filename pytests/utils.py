import json

from rest_framework import serializers
from rest_framework.renderers import JSONRenderer


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
