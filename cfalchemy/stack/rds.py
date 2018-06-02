from . import base


class DBInstance(base.StackResource):

    resource_type = 'AWS::RDS::DBInstance'
    boto_service_name = 'rds'

    @property
    def instance_id(self):
        return self.name

    @base.Base.cached_property
    def describe(self):
        data = self.conn.describe_db_instances(DBInstanceIdentifier=self.instance_id)
        assert len(data['DBInstances']) == 1
        return data['DBInstances'][0]

    @base.Base.cached_property
    def arn(self):
        return self.describe['DBInstanceArn']

    @base.Base.cached_property
    def cfalchemy_uuid(self):
        return self.arn

    @property
    def dns_name(self):
        return self.describe['Endpoint']['Address']

    @property
    def port(self):
        return self.describe['Endpoint']['Port']

    @base.StackResource.cached_property
    def tags(self):
        return base.AwsDict(
            'Key', 'Value',
            getter=lambda: self.conn.list_tags_for_resource(ResourceName=self.arn)['TagList'],
            setter=lambda els: self.conn.add_tags_to_resource(
                ResourceName=self.arn,
                Tags=list(els)
            ),
            deleter=lambda els: self.conn.remove_tags_from_resource(
                ResourceName=self.arn,
                TagKeys=list(el['Key'] for el in els)
            )
        )

    def stop(self):
        try:
            self.conn.stop_db_instance(DBInstanceIdentifier=self.instance_id)
        finally:
            self.clear_cache()

    def start(self):
        try:
            self.conn.start_db_instance(DBInstanceIdentifier=self.instance_id)
        finally:
            self.clear_cache()
