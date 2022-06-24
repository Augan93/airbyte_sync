import time
import io
import csv

from abc import ABC, abstractmethod
from typing import List, Mapping, Any

from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.models import SyncMode


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
                "MaxItems": 50,
                "stream_slice": stream_slice,
            }
            if marker:
                kwargs.update(Marker=marker)

            response = self.read(**kwargs)
            for record in response[self.field]:
                yield record

            if response.get("IsTruncated"):
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
            yield {
                "user_name": user["UserName"],
                "user_id": user["UserId"]
            }


class Roles(AmazonIamStream):
    primary_key = None
    field = "Roles"

    def read(self, **kwargs):
        kwargs.pop("stream_slice")
        return self.client.list_roles(**kwargs)


class RoleAttachedPolicies(AmazonIamStream):
    primary_key = None
    field = "AttachedPolicies"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        role_name = stream_slice["role_name"]
        role_id = stream_slice["role_id"]

        response = self.client.list_attached_role_policies(
            RoleName=role_name,
            **kwargs,
        )
        for record in response[self.field]:
            record.update({
                "RoleName": role_name,
                "RoleId": role_id,
            })
        return response

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ):
        roles = Roles(client=self.client)
        for role in roles.read_records(sync_mode=SyncMode.full_refresh):
            yield {
                "role_name": role["RoleName"],
                "role_id": role["RoleId"]
            }


class UserAttachedPolicies(UserGroups):
    primary_key = None
    field = "AttachedPolicies"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")

        response = self.client.list_attached_user_policies(
            UserName=stream_slice["user_name"],
            **kwargs
        )
        for record in response[self.field]:
            record.update({
                "UserName": stream_slice["user_name"],
                "UserId": stream_slice["user_id"],
            })
        return response


class Groups(AmazonIamStream):
    primary_key = None
    field = "Groups"

    def read(self, **kwargs):
        kwargs.pop("stream_slice")
        return self.client.list_groups(**kwargs)


class GroupPolicies(AmazonIamStream):
    """Inline policies attached to groups"""
    primary_key = None
    field = "PolicyNames"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        response = self.client.list_group_policies(
            GroupName=stream_slice["group_name"],
            **kwargs
        )
        policy_names = response[self.field]
        new_policy_names = []
        for policy_name in policy_names:
            new_policy_names.append({
                "Name": policy_name,
                "GroupName": stream_slice["group_name"],
                "GroupId": stream_slice["group_id"]
            })
        response[self.field] = new_policy_names
        return response

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ):
        groups = Groups(client=self.client)
        for group in groups.read_records(sync_mode=SyncMode.full_refresh):
            yield {
                "group_name": group["GroupName"],
                "group_id": group["GroupId"]
            }


class GroupUsers(GroupPolicies):
    """
    Returns a list of IAM users that are in the specified IAM group
    """
    field = "Users"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        response = self.client.get_group(
            GroupName=stream_slice["group_name"],
            **kwargs
        )
        for record in response[self.field]:
            record["GroupName"] = stream_slice["group_name"]
            record["GroupId"] = stream_slice["group_id"]
        return response


class ManagedPolicies(AmazonIamStream):
    """
    Lists all the managed policies that are available in your Amazon Web Services account, including your own c
    ustomer-defined managed policies and all Amazon Web Services managed policies.
    """
    primary_key = None
    field = "Policies"

    def __init__(self, client, fetch_description: bool = False, only_attached: bool = False):
        super().__init__(client)
        self.fetch_description = fetch_description
        self.only_attached = only_attached

    def read(self, **kwargs):
        kwargs.pop("stream_slice")
        response = self.client.list_policies(
            Scope='All',
            OnlyAttached=self.only_attached,
            **kwargs
        )
        if not self.fetch_description:
            return response

        for record in response[self.field]:
            response_2 = self.client.get_policy(
                PolicyArn=record["Arn"]
            )
            record.update({"Description": response_2["Policy"]["Description"]})
        return response


class PolicyAttachedEntities(AmazonIamStream):

    primary_key = None
    field = "Entities"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        response = self.client.list_entities_for_policy(
            PolicyArn=stream_slice["policy_arn"],
            **kwargs
        )

        new_response = dict(response)
        groups = new_response.pop("PolicyGroups")
        users = new_response.pop("PolicyUsers")
        roles = new_response.pop("PolicyRoles")

        groups = [{"EntityType": "Group",
                   "EntityName": group["GroupName"],
                   "EntityId": group["GroupId"]} for group in groups]
        users = [{"EntityType": "User",
                  "EntityName": user["UserName"],
                  "EntityId": user["UserId"]} for user in users]
        roles = [{"EntityType": "Role",
                  "EntityName": role["RoleName"],
                  "EntityId": role["RoleId"]} for role in roles]

        entities = groups + users + roles

        for entity in entities:
            entity.update({"PolicyName": stream_slice["policy_name"],
                           "PolicyId": stream_slice["policy_id"],
                           "PolicyArn": stream_slice["policy_arn"]})

        new_response[self.field] = entities
        return new_response

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ):
        policies = ManagedPolicies(
            client=self.client,
            fetch_description=False,
            only_attached=True
        )
        for policy in policies.read_records(sync_mode=SyncMode.full_refresh):
            yield {
                "policy_name": policy["PolicyName"],
                "policy_id": policy["PolicyId"],
                "policy_arn": policy["Arn"]
            }


class UserInlinePolicyList(AmazonIamStream):
    """
    Lists the names of the inline policies embedded in the specified IAM user.
    """
    primary_key = None
    field = "PolicyNames"

    def __init__(self, client, user_name: str):
        super().__init__(client=client)
        self.user_name = user_name

    def read(self, **kwargs):
        kwargs.pop("stream_slice")
        response = self.client.list_user_policies(
            UserName=self.user_name,
            **kwargs
        )
        return response


class UserPolicies(AmazonIamStream):
    """
    Get user's inline policy document
    """
    primary_key = None
    field = "UserPolicy"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        response = self.client.get_user_policy(
            UserName=stream_slice["user_name"],
            PolicyName=stream_slice["policy_name"]  # get inline policy name from the Class above
        )
        new_response = dict(response)
        new_response[self.field] = [
            {
                'UserName': new_response.pop("UserName"),
                'PolicyName': new_response.pop("PolicyName"),
                'PolicyDocument': new_response.pop("PolicyDocument")
            }
        ]
        new_response["IsTruncated"] = False
        return new_response

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ):
        users = Users(client=self.client)
        for user in users.read_records(sync_mode=SyncMode.full_refresh):
            user_policy_list = UserInlinePolicyList(
                client=self.client,
                user_name=user["UserName"]
            )
            for policy_name in user_policy_list.read_records(sync_mode=SyncMode.full_refresh):
                yield {
                    "user_name": user["UserName"],
                    "policy_name": policy_name,
                }


class RoleInstanceProfiles(RoleAttachedPolicies):
    primary_key = None
    field = "InstanceProfiles"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        response = self.client.list_instance_profiles_for_role(
            RoleName=stream_slice["role_name"],
            **kwargs
        )
        return response


class UserServiceCredentials(UserGroups):
    primary_key = None
    field = "ServiceSpecificCredentials"

    def read(self, **kwargs):
        stream_slice = kwargs.pop("stream_slice")
        response = self.client.list_service_specific_credentials(
            UserName=stream_slice["user_name"],
        )
        return response


class CredentialReports(Stream):
    primary_key = None
    WAIT_TIME = 1  # seconds

    def __init__(self, client):
        self.client = client

    def generate_report(self):
        while True:
            response = self.client.generate_credential_report()
            if response["State"] == "COMPLETE":
                return True
            time.sleep(self.WAIT_TIME)

    @staticmethod
    def read_csv(content):
        f = io.StringIO(content.decode("utf-8"))
        reader = csv.DictReader(f)
        for row in reader:
            yield row

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ):
        self.generate_report()
        response = self.client.get_credential_report()
        content = response["Content"]
        for record in self.read_csv(content):
            yield record


class OrganizationAccessReports(Stream):
    primary_key = None
    WAIT_TIME = 1  # seconds
    field = "AccessDetails"

    def __init__(self, client, config):
        self.client = client
        self.entity_path = f"{config['organization_id']}/{config['root_id']}"

    def generate_report(self) -> str:
        response = self.client.generate_organizations_access_report(
            EntityPath=self.entity_path,
        )
        return response["JobId"]

    def get_report(self, **kwargs):
        while True:
            response = self.client.get_organizations_access_report(**kwargs)
            if response["JobStatus"] == "IN_PROGRESS":
                time.sleep(self.WAIT_TIME)
            elif response["JobStatus"] == "COMPLETED":
                return response
            elif response["JobStatus"] == "FAILED":
                return {
                    self.field: [],
                    "IsTruncated": False,
                }

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ):
        job_id = self.generate_report()

        pagination_complete = False
        marker = None
        while not pagination_complete:
            kwargs = {
                "MaxItems": 100,
                "JobId": job_id,
            }
            if marker:
                kwargs.update(Marker=marker)

            response = self.get_report(**kwargs)
            for record in response[self.field]:
                yield record

            if response.get("IsTruncated"):
                marker = response["Marker"]
            else:
                pagination_complete = True
