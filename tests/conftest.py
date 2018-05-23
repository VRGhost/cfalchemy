import pytest

from tests import util


@pytest.fixture
def fake_boto3():
    return util.FakeBoto()
