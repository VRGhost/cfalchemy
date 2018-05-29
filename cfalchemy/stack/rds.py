from . import base


class DBInstance(base.Base):

    resource_type = 'AWS::RDS::DBInstance'

    def __init__(self, stack, name):
        super(DBInstance, self).__init__()
        self.name = name
        self.stack = stack
        self.conn = self.stack.boto_client('rds')

    @base.Base.cached_property
    def describe(self):
        data = self.conn.describe_db_instances(DBInstanceIdentifier=self.name)
        assert len(data['DBInstances']) == 1
        return data['DBInstances'][0]
