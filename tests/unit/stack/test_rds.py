import pytest
import mock


class TestDbInstance(object):

    @pytest.fixture()
    def my_instance(self, default_stack):
        return default_stack.resources['Database'].resource

    def test_describe(self, my_instance):
        assert my_instance.describe
        assert my_instance.instance_id == 'sdb6e3j9i18bep'

    def test_simple_props(self, my_instance):
        assert my_instance.dns_name == 'sdb6e3j9i18bep.chayoly0loym.eu-central-1.rds.amazonaws.com'
        assert my_instance.port == 5432

    def test_stop(self, my_instance):
        my_instance.stop()
        my_instance.conn.stop_db_instance.assert_called_with(DBInstanceIdentifier='sdb6e3j9i18bep')

    def test_start(self, my_instance):
        my_instance.start()
        my_instance.conn.start_db_instance.assert_called_with(DBInstanceIdentifier='sdb6e3j9i18bep')

    def test_tags_get(self, my_instance):
        assert dict(my_instance.tags) == {
            'aws:cloudformation:stack-name': 'sooty',
            'CreatedWith': 'create-stack.sh',
            'aws:cloudformation:logical-id': 'Database',
            'aws:cloudformation:stack-id':
                'arn:aws:cloudformation:eu-central-1:424242424242:stack/sooty/479d5820-5842-11e8-88f7-500c52a6ce62',
            'Name': 'sooty Database'
        }
        my_instance.conn.list_tags_for_resource.assert_called_with(
            ResourceName='arn:aws:rds:eu-central-1:424242424242:db:sdb6e3j9i18bep'
        )

    def test_tags_set(self, my_instance):
        my_instance.tags['hello'] = 'world'
        my_instance.conn.add_tags_to_resource.assert_called_with(
            ResourceName=my_instance.arn,
            Tags=[
                {'Key': 'hello', 'Value': 'world'},
            ]
        )

    def test_tags_delete(self, my_instance):
        del my_instance.tags['CreatedWith']
        my_instance.conn.remove_tags_from_resource.assert_called_with(
            ResourceName=my_instance.arn,
            TagKeys=['CreatedWith']
        )
