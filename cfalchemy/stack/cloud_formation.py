"""AWS::CloudFormation::*"""
import re
import boto3
import uuid
from cached_property import cached_property

from . import base


class Stack(base.Base):

    resource_type = 'AWS::CloudFormation::Stack'

    def __init__(self, name, registry, boto_kwargs):
        self._input_name = name
        self.registry = registry
        self._boto_kwargs = dict(boto_kwargs)
        self.conn = self.boto_client('cloudformation')

    def boto_client(self, module):
        return boto3.client(module, **self._boto_kwargs)

    @cached_property
    def describe(self):
        print('describe_fn=', self.conn.describe_stacks)
        return self.conn.describe_stacks(StackName=self._input_name)['Stacks'][0]

    @property
    def stack_id(self):
        return self.describe['StackId']

    @cached_property
    def _parsed_stack_id(self):
        return re.match(
            r'^arn:aws:cloudformation:([\w-]+):(\d+):stack/([\w_-]+)/([a-z\d-]+)$',
            self.stack_id
        ).groups()

    @property
    def cfalchemy_uuid(self):
        return self.describe['StackId']

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
