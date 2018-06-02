"""Utility functions"""
import os
import contextlib
import mock
import yaml

RESOURCES_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources',
)


def load_resource(*path):
    full_path = os.path.join(RESOURCES_ROOT, *path) + ".yaml"
    assert os.path.isfile(full_path), full_path
    with open(full_path, 'r') as fobj:
        return yaml.load(fobj)


class FakeBoto(object):

    current_mock = None

    @contextlib.contextmanager
    def patch(self):
        """A context that patches boto3 into a mock"""
        assert self.current_mock is None, "Only one concurrent mock is permitted"
        with mock.patch('boto3.client') as boto_client_mock:
            out = {
                'client': boto_client_mock
            }
            self.current_mock = out
            try:
                yield out
            finally:
                self.current_mock = None

    def load_resoruce(self, *path):
        return load_resource(*path)
