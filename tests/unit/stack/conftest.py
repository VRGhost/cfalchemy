"""Stack conftest"""

import contextlib
import pytest
import mock


class FakeAwsEnv:

    def __init__(self, fake_boto):
        self.fake_boto = fake_boto
        self.client_mock = mock.Mock(name='FakeAwsEnv::Client::Resource')
        self.resource_config = {}

        from cfalchemy.resource_registry import CFAlchemyResourceRegistry
        self.registry = mock.Mock(name='FakeCFAlchemyResourceRegistry', spec=CFAlchemyResourceRegistry)

    def update(self, config):
        """Update with boto3.client(<key> -> config)"""
        assert isinstance(config, dict)
        self.resource_config.update(config)

    @contextlib.contextmanager
    def activate(self):
        """Context to activate this environment"""
        with self.fake_boto.patch() as boto_patch_handle:
            boto_patch_handle['client'].side_effect = self._get_client_side_effect
            yield self

    def _get_client_side_effect(self, name, *args, **kwargs):
        config = self.resource_config.get(name)
        if config:
            rv = getattr(self.client_mock, name)
            for (name, params) in config.items():
                mock_handle = getattr(rv, name)
                mock_handle.side_effect = lambda *a, **kw: self._get_module_side_effect(mock_handle, params)
        else:
            # No config - return the default return value
            rv = self.client_mock.default
        return rv

    def _get_module_side_effect(self, api_mock, mock_params):
        if callable(mock_params):
            rv = mock_params()
        else:
            raise NotImplementedError(api_mock)
        return rv


@pytest.fixture()
def fake_aws_env(fake_boto3):
    """This is a binding that allows to specify fake responses for the boto3 env"""
    return FakeAwsEnv(fake_boto3)


@pytest.fixture()
def default_fake_aws_env(fake_aws_env, fake_boto3):
    """Default fake AWS envitonemnt"""
    fake_aws_env.update({
        'cloudformation': {
            'describe_stacks': lambda: fake_boto3.load_resoruce('cloudformation', 'describe_stacks'),
        }
    })
    return fake_aws_env
