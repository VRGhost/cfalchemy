import cfalchemy


def test_module_imports():
    assert cfalchemy


def test_stack_can_be_constructed(fake_boto3):
    with fake_boto3.patch() as mocks:
        connection = mocks['client'].return_value

        stack = cfalchemy.client(
            'hello-world', region_name='hello-world-region-42'
        )
        assert not connection.describe_stacks.called
        connection.describe_stacks.return_value = fake_boto3.load_resoruce(
            'cloudformation', 'describe_stacks')

    assert mocks['client'].called
    # accessing .name should trigger a boto call
    assert stack.name == 'hello-world'
    assert connection.describe_stacks.called
    assert stack.aws_account_id == '424242424242'
