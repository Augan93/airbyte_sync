#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import logging
from typing import Tuple, Optional, Any, Mapping
import botocore

from airbyte_cdk.sources import AbstractSource
from .amazon_client import get_amazon_iam_client
from .streams import UserGroups, Users, Roles, RoleAttachedPolicies, UserAttachedPolicies, Groups, GroupPolicies


class SourceAmazonIam(AbstractSource):

    def check_connection(self, logger: logging.Logger, config: Mapping[str, Any]) -> Tuple[bool, Optional[Any]]:
        client = get_amazon_iam_client(config)
        try:
            client.list_groups(
                MaxItems=10
            )
            return True, None
        except botocore.exceptions.ClientError as ex:
            return False, str(ex)

    def streams(self, config: Mapping[str, Any]):
        client = get_amazon_iam_client(config)
        return [
            UserGroups(client=client),
            Users(client=client),
            Roles(client=client),
            RoleAttachedPolicies(client=client),
            UserAttachedPolicies(client=client),
            Groups(client=client),
            GroupPolicies(client=client),
        ]
