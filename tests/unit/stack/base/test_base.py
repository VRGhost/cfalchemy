"""Test stack.base module"""

# import mock
import pytest

import cfalchemy.stack.base


class BoundUUidBase(cfalchemy.stack.base.Base):

    def __init__(self, uuid):
        super(BoundUUidBase, self).__init__()
        self.__uuid__ = uuid

    @property
    def cfalchemy_uuid(self):
        if callable(self.__uuid__):
            rv = self.__uuid__()
        else:
            rv = self.__uuid__
        return rv


class TestBaseUuid:

    def test_repr_no_exceptions(self):
        obj1 = BoundUUidBase('potato1')
        obj2 = BoundUUidBase('potato2')
        obj3 = BoundUUidBase('potato2')

        assert not obj1 == obj2
        assert not obj1 == obj3
        assert obj2 == obj3
        assert 'potato1' in repr(obj1)
        assert 'potato2' in repr(obj2)

    def test_repr_exc(self):
        """Check that bases' repr works even if uuid property explodes"""
        def _err_fn():
            raise Exception('NOOOOOO')
        obj = BoundUUidBase(_err_fn)
        txt = repr(obj)
        assert 'ERROR' in txt


class CachedPropsBase(BoundUUidBase):

    _counter = 0

    @cfalchemy.stack.base.Base.cached_property
    def prop1(self):
        self._counter += 1
        return self._counter

    @cfalchemy.stack.base.Base.cached_property
    def prop2(self):
        self._counter += 1
        return self._counter

    @cfalchemy.stack.base.Base.cached_property
    def prop3(self):
        self._counter += 1
        return self._counter


class TestCachedProps:

    @pytest.fixture
    def obj(self):
        return CachedPropsBase('uuid-42')

    def test_normal_caching(self, obj):
        # Cached property values depend on order of access
        assert obj.prop1 == 1
        assert obj.prop3 == 2
        assert obj.prop2 == 3
        assert obj.prop2 == 3
        assert obj.prop1 == 1
        assert obj.prop3 == 2

    def test_cache_clear(self, obj):
        obj.prop1
        obj.prop2
        obj.prop3
        obj.prop1

        obj.clear_cache()

        assert obj.prop3 == 4
        assert obj.prop2 == 5
        assert obj.prop1 == 6
        assert obj.prop1 == 6
