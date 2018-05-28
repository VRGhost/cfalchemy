"""AWS::CloudFormation::* support"""
import pytest
import uuid

import cfalchemy.stack.cloud_formation as cf


@pytest.fixture()
def my_stack(default_fake_aws_env):
    with default_fake_aws_env.activate() as env:
        stack = cf.Stack('hello-world', env.registry, {})
        yield stack


def test_local_props(my_stack):

    assert my_stack.name == 'hello-world'
    assert my_stack.cfalchemy_uuid == \
        'arn:aws:cloudformation:eu-central-1:424242424242:stack/hello-world/479d5820-1842-12e8-88f7-500c52a6ce62'
    assert my_stack.region == 'eu-central-1'
    assert my_stack.aws_account_id == '424242424242'
    assert my_stack.name == 'hello-world'
    assert my_stack.uuid == uuid.UUID('479d5820-1842-12e8-88f7-500c52a6ce62')

    assert my_stack.capabilities == ('CAPABILITY_IAM', )
    assert my_stack.status == 'UPDATE_COMPLETE'


def test_dict_props(my_stack):
    assert my_stack.outputs['DeployKeyId'] == 'AKIAJC7FGDRH76UPW3LQ'
    assert my_stack.parameters['PriveledgedIp'] == '217.138.75.112/29'
    assert my_stack.tags['CreatedWith'] == 'create-stack.sh'


def test_stack_resources_accessor(my_stack):
    assert len(my_stack.resources) == 79
    for (key, resource) in my_stack.resources.items():
        assert resource.logical_id == key


def test_stack_resource(my_stack):
    logical_id = 'CeleryWorkerCPUAlarmLow'
    resource = my_stack.resources[logical_id]
    assert resource.status == 'UPDATE_COMPLETE'
    assert resource.type == 'AWS::CloudWatch::Alarm'
    assert resource.physical_id == 'sooty-CeleryWorkerCPUAlarmLow-DYOHQBR3UPT9'
    assert logical_id in repr(resource)
