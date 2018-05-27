import mock
import pytest

import cfalchemy.resource_registry
import cfalchemy.stack.base


class FakeCfCls:
    resource_type = None

    def __init__(self, resoure_type):
        self.resource_type = resoure_type


class TestResourceRegisty:

    def test_class_exists(self):
        assert cfalchemy.resource_registry.CFAlchemyResourceRegistry is not None

    @mock.patch('cfalchemy.resource_registry.CFAlchemyResourceRegistry._iter_all_cf_classes')
    def test_duplicate_class_handle(self, iter_cf_mock):
        iter_cf_mock.return_value = (
            FakeCfCls('AWS::hello'),
            FakeCfCls('AWS::hello'),
        )
        with pytest.raises(cfalchemy.resource_registry.RegistryConfigionError) as err:
            cfalchemy.resource_registry.CFAlchemyResourceRegistry()

        assert err.type is cfalchemy.resource_registry.RegistryConfigionError
        assert str(err.value).startswith('Duplicate resource type ')

    @mock.patch('cfalchemy.resource_registry.CFAlchemyResourceRegistry._iter_all_cf_classes')
    def test_incorrect_prefix(self, iter_cf_mock):
        iter_cf_mock.return_value = (
            FakeCfCls('AWS::hello'),
            FakeCfCls('POTATO::world'),
        )
        with pytest.raises(cfalchemy.resource_registry.RegistryConfigionError) as err:
            cfalchemy.resource_registry.CFAlchemyResourceRegistry()

        assert err.type is cfalchemy.resource_registry.RegistryConfigionError
        assert str(err.value).startswith('Unexpected resource type ')

    @mock.patch('cfalchemy.resource_registry.CFAlchemyResourceRegistry._iter_all_cf_classes')
    def test_accessor_funcs(self, iter_cf_mock):
        iter_cf_mock.return_value = (
            FakeCfCls('AWS::hello'),
            FakeCfCls('AWS::world'),
        )
        instance = cfalchemy.resource_registry.CFAlchemyResourceRegistry()

        assert len(instance) == len(iter_cf_mock.return_value)

        for input_cls in iter_cf_mock.return_value:
            assert instance[input_cls.resource_type] is input_cls
            assert input_cls.resource_type in tuple(instance)
            assert input_cls.resource_type in repr(instance)

    def test_iter_all_classes_only_has_stack_classes(self):
        for cls in cfalchemy.resource_registry.CFAlchemyResourceRegistry._iter_all_cf_classes():
            assert issubclass(cls, cfalchemy.stack.base.Base)
