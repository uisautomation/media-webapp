import logging
import json

from rest_framework import serializers

from api import serializers as apiserializers

LOG = logging.getLogger(__name__)


class MediaItemPageSerializer(serializers.Serializer):
    """
    A serialiser for media items which renders one field, ``json_ld``, which is the representation
    of the media item in JSON LD format.

    """
    json_ld = serializers.SerializerMethodField()

    def get_json_ld(self, obj):
        data = apiserializers.MediaSerializer(obj, context=self.context).data
        return json.dumps(data)
