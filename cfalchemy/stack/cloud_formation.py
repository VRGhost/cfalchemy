"""AWS::CloudFormation::*"""
import re
import boto3
import uuid
from frozendict import frozendict

from . import base


class StackResource(base.Base):

    def __init__(self, stack, aws_data):
        super(StackResource, self).__init__()
        self.stack = stack
        self.data = aws_data

    @property
    def status(self):
        return self.data['ResourceStatus']

    @property
    def type(self):
        return self.data['ResourceType']

    @property
    def logical_id(self):
        return self.data['LogicalResourceId']

    @property
    def physical_id(self):
        return self.data['PhysicalResourceId']

    @base.Base.cached_property
    def resource(self):
        """Actual AWS resource handle for this object.

        Raises KeyError if resource type isn't supported yet.
        """
        cls = self.stack.registry[self.type]
        return cls(self.stack, self.physical_id)

    def __repr__(self):
        return "<{} data={}>".format(self.__class__.__name__, self.data)


class Stack(base.Base):

    resource_type = 'AWS::CloudFormation::Stack'

    def __init__(self, name, registry, boto_kwargs):
        super(Stack, self).__init__()
        self._input_name = name
        self.registry = registry
        self._boto_kwargs = dict(boto_kwargs)
        self.conn = self.boto_client('cloudformation')

    def boto_client(self, module):
        return boto3.client(module, **self._boto_kwargs)

    @base.Base.cached_property
    def aws_describe(self):
        return self.conn.describe_stacks(StackName=self._input_name)['Stacks'][0]

    @base.Base.cached_property
    def aws_resources(self):
        return self.conn.describe_stack_resources(StackName=self.name)['StackResources']

    @property
    def stack_id(self):
        return self.aws_describe['StackId']

    @base.Base.cached_property
    def _parsed_stack_id(self):
        return re.match(
            r'^arn:aws:cloudformation:([\w-]+):(\d+):stack/([\w_-]+)/([a-z\d-]+)$',
            self.stack_id
        ).groups()

    @property
    def cfalchemy_uuid(self):
        return self.aws_describe['StackId']

    @property
    def region(self):
        return self._parsed_stack_id[0]

    @property
    def aws_account_id(self):
        return self._parsed_stack_id[1]

    @property
    def name(self):
        return self._parsed_stack_id[2]

    @property
    def uuid(self):
        return uuid.UUID(self._parsed_stack_id[3])

    @property
    def capabilities(self):
        return tuple(self.aws_describe['Capabilities'])

    @property
    def status(self):
        return self.aws_describe['StackStatus']

    @base.Base.cached_property
    def outputs(self):
        return base.AwsDict(
            'OutputKey', 'OutputValue',
            getter=lambda: self.aws_describe['Outputs']
        )

    @base.Base.cached_property
    def parameters(self):
        return base.AwsDict(
            'ParameterKey', 'ParameterValue',
            getter=lambda: self.aws_describe['Parameters']
        )

    @base.Base.cached_property
    def tags(self):
        return base.AwsDict(
            'Key', 'Value',
            getter=lambda: self.aws_describe['Tags']
        )

    @base.Base.cached_property
    def resources(self):
        resources = [
            StackResource(self, data)
            for data in self.aws_resources
        ]
        # logical_ids must be unique in scope of particular stack instance
        return frozendict(
            (res.logical_id, res)
            for res in resources
        )

    def get_resource(self, logical_or_physical_id, default=KeyError):
        for resource in self.resources.values():
            if logical_or_physical_id in (resource.physical_id, resource.logical_id):
                return resource
        # not found
        if default is KeyError:
            raise KeyError(logical_or_physical_id)
        else:
            return default
