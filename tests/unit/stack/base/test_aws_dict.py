import pytest
import mock

import cfalchemy.stack.base.aws_dict as aws_dict


class TestAwsPropsDictComplete:

    def default_getter(self):
        return [
            {'KeyEl': 'val1', 'ValEl': 'val1', 'PropEl': 'prop1'},
            {'KeyEl': 'val2', 'ValEl': 'val2', 'PropEl': 'prop2'},
            {'KeyEl': 'val3', 'ValEl': 'val3', 'PropEl': 'prop3'},
            {'KeyEl': 'val4', 'ValEl': 'val4', 'PropEl': 'prop4'},
        ]

    def test_getter(self):
        tested = aws_dict.AwsPropsDictComplete('KeyEl', self.default_getter)
        assert tested['val1']['ValEl'] == 'val1'
        assert tested['val2']['PropEl'] == 'prop2'
        assert tested['val3'].key == 'val3'

    def test_no_setter_explodes(self):
        tested = aws_dict.AwsPropsDictComplete('KeyEl', self.default_getter)
        assert tested['val1']
        with pytest.raises(NotImplementedError):
            tested['val1']['ValEl'] = 'NewValue'
        with pytest.raises(NotImplementedError):
            tested['val_new'] = {'PropEl': 'hello world!'}
        with pytest.raises(NotImplementedError):
            # This pop() should actually cause element update
            tested['val1'].pop('ValEl')

    def test_no_deleter_explodes(self):
        tested = aws_dict.AwsPropsDictComplete('KeyEl', self.default_getter)
        assert tested['val1']
        with pytest.raises(NotImplementedError):
            del tested['val1']

    def test_setter_one(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsPropsDictComplete('KeyEl', self.default_getter, setter)
        tested['val1']['PropEl'] = "Updated!"
        setter.assert_called_with([{'KeyEl': 'val1', 'ValEl': 'val1', 'PropEl': "Updated!"}])

    def test_setter_multiple(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsPropsDictComplete('KeyEl', self.default_getter, setter)
        with tested.bulk_update():
            tested['val1']['PropEl'] = "Updated!"
            tested['val2']['PropEl'] = "Updated! 2"
            tested['val4']['PropEl'] = "Updated! 4"
        setter.assert_called_with([
            {'KeyEl': 'val1', 'ValEl': 'val1', 'PropEl': "Updated!"},
            {'KeyEl': 'val2', 'ValEl': 'val2', 'PropEl': "Updated! 2"},
            {'KeyEl': 'val4', 'ValEl': 'val4', 'PropEl': "Updated! 4"}
        ])
