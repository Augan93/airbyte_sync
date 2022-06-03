from abc import ABC, abstractmethod
from typing import List, Mapping, Any

from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.models import AirbyteStream, SyncMode


class AmazonIamStream(Stream, ABC):
    def __init__(self, client):
        self.client = client


class UserGroups(AmazonIamStream):
    primary_key = None

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ):
        response = self.client.list_groups_for_user(
            UserName='Augan',
            # Marker='string',
            MaxItems=123
        )
        for group in response["Groups"]:
            yield group
