import pytest
import mock

import cfalchemy.stack.ec2 as ec2


class TestSubnet(object):

    @pytest.fixture()
    def my_subnet(self, default_stack):
        return default_stack.resources['PublicSubnet1'].resource

    def test_describe(self, my_subnet):
        assert my_subnet.describe
        assert my_subnet.cfalchemy_uuid == 'cfalchemy::ec2::subnet::subnet-dfffd2b4'

    def test_simple_props(self, my_subnet):
        assert my_subnet.subnet_id == 'subnet-dfffd2b4'
        assert my_subnet.availability_zone == 'eu-central-1a'


class TestInstance(object):

    @pytest.fixture()
    def my_instance(self, default_stack):
        return default_stack.resources['Bastion'].resource

    def test_describe(self, my_instance):
        assert my_instance.describe
        assert my_instance.cfalchemy_uuid == 'cfalchemy::ec2::instance::i-007d05f94c3bb8027'

    def test_simple_props(self, my_instance):
        assert my_instance.instance_id == 'i-007d05f94c3bb8027'
        assert my_instance.dns_name == 'ip-10-138-10-92.eu-central-1.compute.internal'
        assert my_instance.public_ip == '18.196.81.235'
        assert my_instance.private_ip == '10.138.10.92'

    @pytest.mark.parametrize('state_code, expected_state', [
        (0, 'pending'),
        (16, 'running'),
        (32, 'shutting_down'),
        (48, 'terminated'),
        (64, 'stopping'),
        (80, 'stopped'),
    ])
    def test_instance_state_checks(self, my_instance, state_code, expected_state):
        state_enum = ec2.InstanceState[expected_state]

        with mock.patch.dict(my_instance.describe, {'State': {'Code': state_code}}):
            assert my_instance.state == state_enum
            for state_attr in (
                'pending',
                'running',
                'shutting_down',
                'terminated',
                'stopping',
                'stopped',
            ):
                if state_attr == expected_state:
                    assert getattr(my_instance, state_attr) is True
                else:
                    assert getattr(my_instance, state_attr) is False

    def test_instance_start(self, my_instance):
        my_instance.describe
        my_instance.describe
        my_instance.describe
        my_instance.start()
        my_instance.describe

        my_instance.conn.start_instances(InstanceIds=[my_instance.name])
        assert my_instance.conn.describe_instances.call_count == 2, \
            "Describe called two times due to cachin & cache purge"

    def test_instance_stop(self, my_instance):
        my_instance.describe
        my_instance.describe
        my_instance.describe
        my_instance.stop()
        my_instance.describe

        my_instance.conn.stop_instances(InstanceIds=[my_instance.name])
        assert my_instance.conn.describe_instances.call_count == 2, \
            "Describe called two times due to cachin & cache purge"

    def test_subnet(self, my_instance):
        assert my_instance.subnet.cfalchemy_uuid == 'cfalchemy::ec2::subnet::subnet-dfffd2b4'
