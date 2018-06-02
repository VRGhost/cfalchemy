import pytest

from tests.unit import util


@pytest.fixture()
def fake_boto3():
    return util.FakeBoto()


@pytest.fixture()
def boto_client_mock(fake_boto3):
    return fake_boto3.current_mock
