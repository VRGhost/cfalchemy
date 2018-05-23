"""Base class for all AWS resources"""
import traceback

from abc import ABC, abstractmethod


class Base(ABC):

    resource_type = "<Override with AWS resource type>"

    @property
    @abstractmethod
    def cfalchemy_uuid(self):
        """This property should return an unique string for each resource in the stack"""
        raise NotImplementedError

    def __eq__(self, other):
        return self.cfalchemy_uuid == other.cfalchemy_uuid

    def __repr__(self):
        try:
            uuid = self.cfalchemy_uuid
        except Exception:
            print('------ ERROR IN REPR -------')
            traceback.print_exc()
            uuid = '!!!! ERROR !!!!'

        return "<{}.{} uuid={!r}>".format(
            self.__module__,
            self.__class__.__name__,
            uuid,
        )
