"""This object contains mapping of all AWS resource types to classes objectifying them."""

import collections

import cfalchemy.stack


class CFAlchemyResourceRegistry(collections.Mapping):

    _registry = None

    def __init__(self):
        _registry = {}
        for cls in (
            cfalchemy.stack.cloud_formation.Stack,
        ):
            resource_type = cls.resource_type
            if resource_type in _registry:
                raise Exception('Duplicate resource type {!r}'.format(resource_type))
            if not resource_type.startswith('AWS::'):
                raise Exception('Unexpected resource type {!r}'.format(resource_type))
            _registry[resource_type] = cls
        self._registry = _registry

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
