"""Client module, represents logical session/connection"""

import cfalchemy.resource_registry

def client(stack_name, **boto_kwargs):
    """Open AWS stack connection"""
    registry = cfalchemy.resource_registry.CFAlchemyResourceRegistry()
    stack_cls = registry['AWS::CloudFormation::Stack']
    return stack_cls(stack_name, registry, boto_kwargs=boto_kwargs)
