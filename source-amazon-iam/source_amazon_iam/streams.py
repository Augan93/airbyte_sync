from abc import ABC, abstractmethod
from typing import List, Mapping, Any

from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.models import AirbyteStream, SyncMode


class AmazonIamStream(Stream, ABC):
    def __init__(self, client):
        self.client = client

    @property
    @abstractmethod
    def field(self):
        pass

    @abstractmethod
    def read(self, **kwargs):
        pass

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ):
        pagination_complete = False
        marker = None
        while not pagination_complete:
            kwargs = {
                # "PathPrefix": "string",
                "MaxItems": 1,
                "stream_slice": stream_slice,
            }
            if marker:
                kwargs.update(Marker=marker)

            response = self.read(**kwargs)
            for record in response[self.field]:
                yield record

            if response["IsTruncated"]:
                marker = response["Marker"]
            else:
                pagination_complete = True


class Users(AmazonIamStream):
    primary_key = None
    field = "Users"

    def read(self, **kwargs):
        kwargs.pop("stream_slice")
        return self.client.list_users(**kwargs)


class UserGroups(AmazonIamStream):
    primary_key = None
    field = "Groups"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")

        response = self.client.list_groups_for_user(
            UserName=stream_slice["user_name"],
            **kwargs,
        )
        for record in response[self.field]:
            record.update({"UserName": stream_slice["user_name"]})
        return response

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ):
        users = Users(client=self.client)
        for user in users.read_records(sync_mode=SyncMode.full_refresh):
            yield {"user_name": user["UserName"]}


class Roles(AmazonIamStream):
    primary_key = None
    field = "Roles"

    def read(self, **kwargs):
        kwargs.pop("stream_slice")
        return self.client.list_roles(**kwargs)
