from django.http import HttpRequest
from django.utils.timezone import now
from rest_framework.views import APIView

from drf_metadata.meta import MetaData
from pytests.test_app.models import CallableDefault
from pytests.utils import force_evaluate


class MyAPIView(APIView):
    def get_view_description(self, html=False):
        return 'description'


class CallableDefaultMetaData(MetaData):
    model = CallableDefault


class CallableBugTest:
    def test__should_call_default_if_default_is_callable(self):
        _metadata = CallableDefaultMetaData().determine_metadata(HttpRequest(), MyAPIView())
        metadata = force_evaluate(_metadata)

        assert metadata['fields'][0]['default'] == now().date().isoformat()
