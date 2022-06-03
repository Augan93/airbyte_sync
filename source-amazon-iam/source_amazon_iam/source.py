#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import logging
from typing import Tuple, Optional, Any, Mapping
import botocore

from airbyte_cdk.sources import AbstractSource
from .amazon_client import get_amazon_iam_client


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
        return []
