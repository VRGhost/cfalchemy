import pytest

from tests.unit import util


@pytest.fixture
def fake_boto3():
    return util.FakeBoto()
