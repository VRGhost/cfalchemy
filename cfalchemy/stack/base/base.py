"""Base class for all AWS resources"""
from abc import ABCMeta, abstractproperty

import logging
import functools
import threading
from cached_property import cached_property as orig_cached_prop

log = logging.getLogger(__name__)


class Base(object):
    __metaclass__ = ABCMeta

    resource_type = "<Override with AWS resource type>"
    _cached_properties = None
    _lock = None

    def __init__(self):
        self._lock = threading.Lock()
        self._cached_properties = set()

    @abstractproperty
    def cfalchemy_uuid(self):
        """This property should return an unique string for each resource in the stack"""
        raise NotImplementedError

    def __eq__(self, other):
        return self.cfalchemy_uuid == other.cfalchemy_uuid

    def __repr__(self):
        try:
            uuid = self.cfalchemy_uuid
        except Exception:
            log.exception('------ ERROR IN REPR -------')
            uuid = '!!!! ERROR !!!!'

        return "<{}.{} uuid={!r}>".format(
            self.__module__,
            self.__class__.__name__,
            uuid,
        )

    def clear_cache(self):
        """Delete all cached data, forcing re-sync with the AWS"""
        with self._lock:
            for name in self._cached_properties:
                self.__dict__.pop(name, None)
            self._cached_properties.clear()

    @staticmethod
    def cached_property(func):
        """Same as `cached_property.cached_property decorator`

        But also updates an index of cached properties in this object so all of them can be nullified when needed.
        """

        @orig_cached_prop
        @functools.wraps(func)
        def _wrapper_(self):
            out = func(self)
            # Update list of cached properties (if prev statement didn't raise an exceptiopn)
            with self._lock:
                self._cached_properties.add(func.__name__)
            return out

        return _wrapper_


class StackResource(Base):
    """Generic stack resource with generic __init__ args"""

    boto_service_name = 'name of the boto3 service for used to access this resource'

    def __init__(self, stack, name):
        """
        :param stack: parent stack object
        :param name: unique resource name/id
        """
        super(StackResource, self).__init__()
        self.name = name
        self.stack = stack

    cached_property = Base.cached_property

    @cached_property
    def conn(self):
        """Boto3 connection object"""
        return self.stack.boto_client(self.boto_service_name)
