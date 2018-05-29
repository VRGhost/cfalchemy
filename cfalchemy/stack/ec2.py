from . import base


class ECInstance(base.Base):

    resource_type = 'AWS::EC2::Instance'

    def __init__(self, stack, name):
        super(ECInstance, self).__init__()
        self.name = name
        self.stack = stack
        self.conn = self.stack.boto_client('ec2')

    @base.Base.cached_property
    def describe(self):
        res = self.conn.describe_instances(InstanceIds=[self.name])['Reservations']
        assert len(res) == 1
        assert len(res[0]['Instances']) == 1
        return res[0]['Instances'][0]


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
