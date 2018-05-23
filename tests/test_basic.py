import cfalchemy


def test_module_imports():
    assert cfalchemy


def test_stack_can_be_constructed(fake_boto3):
    with fake_boto3.patch() as mocks:
        stack = cfalchemy.client(
            'hello-world', region_name='hello-world-region-42'
        )
        assert not mocks['connection'].describe_stacks.called
        mocks['connection'].describe_stacks.return_value = fake_boto3.load_resoruce(
            'cloud_formation', 'describe_stacks')

    assert mocks['client'].called
    # accessing .name should trigger a boto call
    assert stack.name == 'hello-world'
    assert mocks['connection'].describe_stacks.called
