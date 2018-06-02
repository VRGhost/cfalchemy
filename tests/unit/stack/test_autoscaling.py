import pytest
import mock


import cfalchemy.stack.autoscaling


class TestASG(object):

    @pytest.fixture()
    def my_asg(self, default_stack):
        return default_stack.resources['DevToolsASG'].resource

    def test_describe(self, my_asg):
        assert my_asg.describe
        assert my_asg.name == 'sooty-DevToolsASG-199RU6P9O1375'

    def test_simple_props(self, my_asg):
        assert my_asg.arn == (
            'arn:aws:autoscaling:eu-central-1:424242424242:autoScalingGroup:'
            'afe5c7f9-ec77-4c71-9a65-472cffd26e78:autoScalingGroupName/sooty-DevToolsASG-199RU6P9O1375'
        )
        assert my_asg.min_size == 1
        assert my_asg.max_size == 100
        assert my_asg.desired_capacity == 2

    def test_tags_get(self, my_asg):
        assert dict(my_asg.tags) == {
            'CreatedWith': 'create-stack.sh',
            'Name': 'sooty Dev tools',
            'aws:cloudformation:logical-id': 'DevToolsASG',
            'aws:cloudformation:stack-id': (
                'arn:aws:cloudformation:eu-central-1:424242424242:stack/sooty/479d5820-5842-11e8-88f7-500c52a6ce62'
            ),
            'aws:cloudformation:stack-name': 'sooty'
        }

    def test_tags_update(self, my_asg):
        my_asg.tags['Name'] = 'Hello World'
        my_asg.conn.create_or_update_tags.assert_called_with(Tags=[
            {
                'Key': 'Name',
                'PropagateAtLaunch': True,
                'ResourceId': my_asg.name,
                'ResourceType': 'auto-scaling-group',
                'Value': 'Hello World'
            }
        ])

    def test_tags_delete(self, my_asg):
        del my_asg.tags['Name']
        my_asg.conn.delete_tags.assert_called_with(Tags=[
            {
                'Key': 'Name',
                'ResourceId': my_asg.name,
                'ResourceType': 'auto-scaling-group',
            }
        ])

    def test_instances(self, my_asg):
        assert len(my_asg.instances) == 1
        handle = my_asg.instances[0]

        assert handle.availability_zone == 'eu-central-1a'
        assert handle.health_status == cfalchemy.stack.autoscaling.AutoScalingInstanceHealth.Healthy
        assert handle.launch_configuration_name == 'sooty-DevToolsInstanceLaunchConfig-1RS4F6JY5F93M'
        assert handle.lifecycle_state == cfalchemy.stack.autoscaling.AutoScalingInstanceStates.InService
        assert handle.protected_from_scale_in is False
        assert handle.instance_id == 'i-00ed09c06862f64eb'
        assert handle.instance.instance_id == handle.instance_id
