from enum import Enum

from . import base


class InstanceState(Enum):
    """
    Instance states from https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
    """
    pending = 0
    running = 16
    shutting_down = 32
    terminated = 48
    stopping = 64
    stopped = 80


class ECInstance(base.StackResource):

    resource_type = 'AWS::EC2::Instance'
    boto_service_name = 'ec2'

    @property
    def instance_id(self):
        return self.name

    @base.StackResource.cached_property
    def describe(self):
        print(self.conn.describe_instances)
        res = self.conn.describe_instances(InstanceIds=[self.instance_id])['Reservations']
        assert len(res) == 1
        assert len(res[0]['Instances']) == 1
        return res[0]['Instances'][0]

    @base.StackResource.cached_property
    def cfalchemy_uuid(self):
        # EC2 instances don't have ARNs
        return "cfalchemy::ec2::{}".format(self.name)

    @property
    def dns_name(self):
        return self.describe['PrivateDnsName']

    @property
    def subnet(self):
        return self.stack[self.describe['SubnetId']]

    @property
    def public_ip(self):
        return self.describe['PublicIpAddress']

    @property
    def private_ip(self):
        return self.describe['PrivateIpAddress']

    # @util.tags.property
    # def tags(self):
    #     return {
    #         'getter': lambda: self.describe['Tags'],
    #         'setter': lambda els: self.conn.create_tags(
    #             Resources=[
    #                 self.instance_id
    #             ],
    #             Tags=list(els)
    #         ),
    #         'deleter': lambda els: self.conn.delete_tags(
    #             Resources=[
    #                 self.instance_id
    #             ],
    #             Tags=list(els)
    #         )
    #     }

    def stop(self):
        """Stop the instance"""
        try:
            self.conn.stop_instances(InstanceIds=[self.instance_id])
        finally:
            self.clear_cache()

    def start(self):
        try:
            self.conn.start_instances(InstanceIds=[self.instance_id])
        finally:
            self.clear_cache()

    # Instance states

    @property
    def state(self):
        return InstanceState(self.describe['State']['Code'])

    pending = property(lambda self: self.state == InstanceState.pending)
    running = property(lambda self: self.state == InstanceState.running)
    shutting_down = property(lambda self: self.state == InstanceState.shutting_down)
    terminated = property(lambda self: self.state == InstanceState.terminated)
    stopping = property(lambda self: self.state == InstanceState.stopping)
    stopped = property(lambda self: self.state == InstanceState.stopped)


class Subnet(base.Base):

    resource_type = 'AWS::EC2::Subnet'

    def __init__(self, stack, name):
        super(Subnet, self).__init__()
        self.name = name
        self.stack = stack
        self.conn = self.stack.boto_client('ec2')

    @base.Base.cached_property
    def describe(self):
        return self.conn.describe_subnets(SubnetIds=[self.name])['Subnets'][0]
