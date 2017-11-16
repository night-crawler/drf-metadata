from django.http import HttpRequest
from django.utils.timezone import now
from rest_framework.views import APIView

from drf_metadata.meta import MetaData
from pytests.test_app.models import CallableDefault, Integers
from pytests.utils import force_evaluate, get_field_by_name


class MyAPIView(APIView):
    def get_view_description(self, html=False):
        return 'description'


class CallableDefaultMetaData(MetaData):
    model = CallableDefault


# noinspection PyMethodMayBeStatic
class CallableBugTest:
    def test__should_call_default_if_default_is_callable(self):
        _metadata = CallableDefaultMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert metadata['fields'][0]['default'] == now().date().isoformat()


# ======================================================================================================================


class IntegersMetaData(MetaData):
    model = Integers


# noinspection PyMethodMayBeStatic
class IntegersMissingOptionsTest:
    def test__decimal_options_are_present_in_metadata(self):
        _metadata = IntegersMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        field = get_field_by_name(metadata, 'f_decimal')
        assert 'decimal_places' in field
        assert 'max_digits' in field
