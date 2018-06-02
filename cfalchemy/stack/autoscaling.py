from enum import Enum
from cached_property import cached_property

from . import base, ec2


class AutoScalingInstanceStates(Enum):
    Pending = "Pending"
    InService = "InService"
    Terminating = "Terminating"
    Terminated = "Terminated"
    Detaching = "Detaching"
    Detached = "Detached"
    EnteringStandby = "EnteringStandby"
    Standby = "Standby"


class AutoScalingInstanceHealth(Enum):
    Healthy = "Healthy"
    Unhealthy = "Unhealthy"


class AutoScalingInstance(object):

    def __init__(self, parent, data):
        self._parent = parent
        self._data = data

    availability_zone = property(lambda self: self._data['AvailabilityZone'])
    health_status = property(lambda self: AutoScalingInstanceHealth[self._data['HealthStatus']])
    launch_configuration_name = property(lambda self: self._data['LaunchConfigurationName'])
    lifecycle_state = property(lambda self: AutoScalingInstanceStates[self._data['LifecycleState']])
    protected_from_scale_in = property(lambda self: self._data['ProtectedFromScaleIn'])
    instance_id = property(lambda self: self._data['InstanceId'])

    @cached_property
    def instance(self):
        return ec2.ECInstance(self._parent.stack, self.instance_id)


class AutoScalingGroup(base.StackResource):

    resource_type = 'AWS::AutoScaling::AutoScalingGroup'
    boto_service_name = 'autoscaling'

    @base.Base.cached_property
    def describe(self):
        return self.conn.describe_auto_scaling_groups(AutoScalingGroupNames=[self.name])['AutoScalingGroups'][0]

    @base.Base.cached_property
    def arn(self):
        return self.describe['AutoScalingGroupARN']

    @base.Base.cached_property
    def cfalchemy_uuid(self):
        return self.arn

    @property
    def instances(self):
        return tuple(
            AutoScalingInstance(self, el)
            for el in self.describe['Instances']
        )

    @property
    def min_size(self):
        return self.describe['MinSize']

    @property
    def max_size(self):
        return self.describe['MaxSize']

    @property
    def desired_capacity(self):
        return self.describe['DesiredCapacity']

    def update(self, **params):
        self.conn.update_auto_scaling_group(
            AutoScalingGroupName=self.name,
            **params
        )
        self.clear_cache()

    @base.StackResource.cached_property
    def tags(self):
        def update_asg_tags(tags):
            out = []
            for el in tags:
                el_copy = el.copy()
                el_copy.update(
                    ResourceId=self.name,
                    ResourceType='auto-scaling-group',
                )
                out.append(el_copy)
            return out

        return base.AwsDict(
            'Key', 'Value',
            getter=lambda: self.describe['Tags'],
            setter=lambda els: self.conn.create_or_update_tags(Tags=update_asg_tags(els)),
            deleter=lambda els: self.conn.delete_tags(
                Tags=[
                    {'Key': el['Key'], 'ResourceId': self.name, 'ResourceType': 'auto-scaling-group'}
                    for el in els
                ]
            ),
            on_cache_purged=lambda: self.clear_cache(),
        )
