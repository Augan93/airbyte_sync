import boto3


def get_amazon_iam_client(config):
    return boto3.client(
        'iam',
        aws_access_key_id=config["aws_access_key_id"],
        aws_secret_access_key=config["aws_secret_access_key"],
    )
