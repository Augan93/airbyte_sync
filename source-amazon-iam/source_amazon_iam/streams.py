from abc import ABC, abstractmethod
from typing import List, Mapping, Any

from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.models import AirbyteStream, SyncMode


class AmazonIamStream(Stream, ABC):
    def __init__(self, client):
        self.client = client


class Users(AmazonIamStream):
    primary_key = None

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
            kwags = {
                # "PathPrefix": "string",
                "MaxItems": 1,
            }
            if marker:
                kwags.update(Marker=marker)
            response = self.client.list_users(**kwags)
            for user in response["Users"]:
                yield user

            if response["IsTruncated"]:
                marker = response["Marker"]
            else:
                pagination_complete = True


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
            UserName=stream_slice["user_name"],
            # Marker='string',
            MaxItems=1
        )
        for group in response["Groups"]:
            yield group

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ):  # TODO
        users = Users(client=self.client)
        for user in users.read_records(sync_mode=SyncMode.full_refresh):
            yield {"user_name": user["UserName"]}
