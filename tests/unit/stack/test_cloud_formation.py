"""AWS::CloudFormation::* support"""
import uuid

import cfalchemy.stack.cloud_formation as cf


def test_props(default_fake_aws_env):
    with default_fake_aws_env.activate() as env:
        stack = cf.Stack('hello-world', env.registry, {})
        assert stack.name == 'hello-world'
        assert stack.cfalchemy_uuid == \
            'arn:aws:cloudformation:eu-central-1:424242424242:stack/hello-world/479d5820-1842-12e8-88f7-500c52a6ce62'
        assert stack.region == 'eu-central-1'
        assert stack.aws_account_id == '424242424242'
        assert stack.name == 'hello-world'
        assert stack.uuid == uuid.UUID('479d5820-1842-12e8-88f7-500c52a6ce62')

        assert stack.capabilities == ('CAPABILITY_IAM', )
