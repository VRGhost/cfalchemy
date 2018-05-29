"""This object contains mapping of all AWS resource types to classes objectifying them."""

import collections

import cfalchemy.stack


class RegistryConfigionError(Exception):
    """Generic registry configuration error"""


class CFAlchemyResourceRegistry(collections.Mapping):

    _registry = None

    def __init__(self):
        _registry = {}
        for cls in self._iter_all_cf_classes():
            resource_type = cls.resource_type
            if resource_type in _registry:
                raise RegistryConfigionError('Duplicate resource type {!r}'.format(resource_type))
            if not resource_type.startswith('AWS::'):
                raise RegistryConfigionError('Unexpected resource type {!r}'.format(resource_type))
            _registry[resource_type] = cls
        self._registry = _registry

    @staticmethod
    def _iter_all_cf_classes():
        """This method just returns a list of all CF class objects known to the cfalchemy library"""
        return (
            cfalchemy.stack.cloud_formation.Stack,
            cfalchemy.stack.ec2.ECInstance,
            cfalchemy.stack.ec2.Subnet,
            cfalchemy.stack.rds.DBInstance,
        )

    def __getitem__(self, name):
        return self._registry[name]

    def __iter__(self):
        return iter(self._registry)

    def __len__(self):
        return len(self._registry)

    def __repr__(self):
        return '<{}.{} supports={}>'.format(
            self.__module__,
            self.__class__.__name__,
            list(sorted(self._registry.keys()))
        )
