import pytest
import mock
import threading

import cfalchemy.stack.base.aws_dict as aws_dict


def unordered_equal(list1, list2):
    list1 = tuple(list1)
    list2 = tuple(list2)
    for any_el in (list1 + list2):
        if not any(
            any_el == l1_el
            for l1_el in list1
        ):
            # print("{!r} not present in {}".format(any_el, list1))
            return False
        if not any(
            any_el == l2_el
            for l2_el in list2
        ):
            # print("{!r} not present in {}".format(any_el, list2))
            return False
    return True


class TestAwsAdvancedDict:

    def default_getter(self):
        return [
            {'KeyEl': 'val1', 'ValEl': 'val1', 'PropEl': 'prop1'},
            {'KeyEl': 'val2', 'ValEl': 'val2', 'PropEl': 'prop2'},
            {'KeyEl': 'val3', 'ValEl': 'val3', 'PropEl': 'prop3'},
            {'KeyEl': 'val4', 'ValEl': 'val4', 'PropEl': 'prop4'},
        ]

    def test_getter(self):
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter)
        assert tested['val1']['ValEl'] == 'val1'
        assert tested['val2']['PropEl'] == 'prop2'
        assert tested['val3'].key == 'val3'
        assert len(tested) == 4
        assert set(tested) == set(['val1', 'val2', 'val3', 'val4'])

    def test_no_setter_explodes(self):
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter)
        assert tested['val1']
        with pytest.raises(NotImplementedError):
            tested['val1']['ValEl'] = 'NewValue'
        with pytest.raises(NotImplementedError):
            tested['val_new'] = {'PropEl': 'hello world!'}
        with pytest.raises(NotImplementedError):
            # This pop() should actually cause element update
            tested['val1'].pop('ValEl')

    def test_no_deleter_explodes(self):
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter)
        assert tested['val1']
        with pytest.raises(NotImplementedError):
            del tested['val1']

    def test_setter_one(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter)
        tested['val1']['PropEl'] = "Updated!"
        setter.assert_called_with([{'KeyEl': 'val1', 'ValEl': 'val1', 'PropEl': "Updated!"}])

    def test_setter_multiple(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter)
        with tested.bulk_update():
            tested['val1']['PropEl'] = "Updated!"
            tested['val2']['PropEl'] = "Updated! 2"
            tested['val4']['PropEl'] = "Updated! 4"
            tested['new_val'] = {"ValEl": "hi there"}

        setter.assert_called_once()
        assert unordered_equal(
            setter.call_args[0][0],
            [
                {'KeyEl': 'val1', 'ValEl': 'val1', 'PropEl': "Updated!"},
                {'KeyEl': 'val2', 'ValEl': 'val2', 'PropEl': "Updated! 2"},
                {'KeyEl': 'val4', 'ValEl': 'val4', 'PropEl': "Updated! 4"},
                {'KeyEl': 'new_val', 'ValEl': "hi there"}
            ]
        )

    def test_deleter(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter, deleter)
        tested.pop('val1')
        deleter.assert_called_with([{'KeyEl': 'val1'}])

    def test_deleter_multiple(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter, deleter)
        with tested.bulk_update():
            tested.pop('val1')
            del tested['val3']

        assert unordered_equal(
            deleter.call_args[0][0],
            [
                {'KeyEl': 'val1'},
                {'KeyEl': 'val3'},
            ]
        )

    def test_repr(self):
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter)
        assert 'val1' in repr(tested)
        assert 'val2' in repr(tested)

    def test_multithreaded_update(self):
        call_args = []

        def on_set(updates):
            # Magic mock doesn't work with threading properly
            # ( https://stackoverflow.com/questions/39332139/thread-safe-version-of-mock-call-count )
            # Hence this workaround
            call_args.append(updates)

        setter = mock.MagicMock()
        setter.side_effect = on_set
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter)
        ready_to_update = threading.Event()

        master_thread_update = dict(
            val1={'ValEl': 'master_thread'},
            val2={'ValEl': 'master_thread'},
            val3={'ValEl': 'master_thread'},
        )

        child_thread_update = dict(
            val1={'ValEl': 'child_thread'},
            val2={'ValEl': 'child_thread'},
            val3={'ValEl': 'child_thread'},
        )

        def _run():
            ready_to_update.set()
            for _ in range(1000):
                tested.update(**child_thread_update)

        t = threading.Thread(target=_run)
        t.start()
        # attempt to call the update function in parallel
        ready_to_update.wait()
        for _ in range(1000):
            tested.update(**master_thread_update)
        # Wait for the child thread to terminate
        t.join()

        assert len(call_args) == 2000, "1k for master thread adn 1k for child thread"

        expected_master_update_call = [
            {'KeyEl': 'val1', 'ValEl': 'master_thread'},
            {'KeyEl': 'val2', 'ValEl': 'master_thread'},
            {'KeyEl': 'val3', 'ValEl': 'master_thread'},
        ]

        expected_child_update_call = [
            {'KeyEl': 'val1', 'ValEl': 'child_thread'},
            {'KeyEl': 'val2', 'ValEl': 'child_thread'},
            {'KeyEl': 'val3', 'ValEl': 'child_thread'},
        ]

        for update_dict in call_args:
            # Each update call is one or the other, not something inbetween and corrupted.
            if unordered_equal(expected_master_update_call, update_dict):
                pass  # all is good - this is pure master call
            elif unordered_equal(expected_child_update_call, update_dict):
                pass  # all is good - this is pure child update call
            else:
                # Failure - this is a mix of two
                assert False, update_dict

    def test_uncomitted_items_view(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter, deleter)

        orig_len = len(tested)
        with tested.bulk_update():
            tested['val1'] = {'ValEl': 'updated'}
            del tested['val2']

            assert tested['val1'] == {'ValEl': 'updated'}
            assert 'val2' not in tested
            assert len(tested) == orig_len - 1

    def test_cb_setters(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter)
        assert tested._setter_fn is None
        assert tested._deleter_fn is None

        tested.setter(setter)
        tested.deleter(deleter)

        assert tested._setter_fn is setter
        assert tested._deleter_fn is deleter

    def test_bulk_update_rollback(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter)
        tested.setter(setter)

        with tested.bulk_update():
            tested['update_1.0'] = {'ValEl': 'build_update_ctx1'}
            with tested.bulk_update():
                tested['update_2.0'] = {'ValEl': 'build_update_ctx2'}
                try:
                    with tested.bulk_update():
                        tested['update_3.0'] = {'ValEl': 'build_update_ctx3'}
                        raise KeyError('Something went wrong')
                except KeyError:
                    # ... recovery happened here
                    pass
                tested['update_2.1'] = {'ValEl': 'build_update_ctx2'}
            tested['update_1.1'] = {'ValEl': 'build_update_ctx1'}

        assert setter.call_count == 1, "only outermost ctx called the setter"
        assert unordered_equal(
            setter.call_args[0][0],
            [
                {'KeyEl': 'update_1.0', 'ValEl': 'build_update_ctx1'},
                {'KeyEl': 'update_1.1', 'ValEl': 'build_update_ctx1'},
                {'KeyEl': 'update_2.0', 'ValEl': 'build_update_ctx2'},
                {'KeyEl': 'update_2.1', 'ValEl': 'build_update_ctx2'},
            ]
        )

    def test_cache_purge_cb_on_update(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        on_purge = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter, deleter, on_purge)

        tested['update_1.0'] = {'ValEl': 'build_update_ctx1'}
        assert on_purge.called

    def test_cache_purge_cb_on_delete(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        on_purge = mock.MagicMock()
        tested = aws_dict.AwsAdvancedDict('KeyEl', self.default_getter, setter, deleter, on_purge)

        tested.pop('val2')
        assert on_purge.called


class TestAwsDict:

    def default_getter(self):
        return [
            {'KeyEl': 'val1', 'ValEl': 'TestAwsDict-val1', 'PropEl': 'TestAwsDict-prop1'},
            {'KeyEl': 'val2', 'ValEl': 'TestAwsDict-val2', 'PropEl': 'TestAwsDict-prop2'},
            {'KeyEl': 'val3', 'ValEl': 'TestAwsDict-val3', 'PropEl': 'TestAwsDict-prop3'},
            {'KeyEl': 'val4', 'ValEl': 'TestAwsDict-val4', 'PropEl': 'TestAwsDict-prop4'},
        ]

    def test_base(self):
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter)
        assert tested['val1'] == 'TestAwsDict-val1'
        assert tested['val4'] == 'TestAwsDict-val4'
        assert tested.full['val2'] == {'ValEl': 'TestAwsDict-val2', 'PropEl': 'TestAwsDict-prop2'}
        assert 'val3' in repr(tested)
        assert len(tested) == 4
        assert set(iter(tested)) == set(['val1', 'val2', 'val3', 'val4'])

    def test_setter_amend(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter, setter)
        tested['val3'] = 'potato'
        assert unordered_equal(
            setter.call_args[0][0],
            [
                {'KeyEl': 'val3', 'ValEl': 'potato', 'PropEl': 'TestAwsDict-prop3'},
            ]
        )

    def test_setter_create(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter, setter)
        tested['val-new'] = 'potato'
        assert unordered_equal(
            setter.call_args[0][0],
            [
                {'KeyEl': 'val-new', 'ValEl': 'potato'},
            ]
        )

    def test_delete(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter, setter, deleter)
        del tested['val1']
        assert not setter.called
        assert unordered_equal(
            deleter.call_args[0][0],
            [
                {'KeyEl': 'val1'},
            ]
        )

    def test_handler_assigment(self):
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter)
        setter = mock.MagicMock()
        deleter = mock.MagicMock()

        tested.setter(setter)
        tested.deleter(deleter)

        assert tested.full._deleter_fn is deleter
        assert tested.full._setter_fn is setter

    def test_bulk_update(self):
        setter = mock.MagicMock()
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter, setter)
        with tested.bulk_update():
            tested['val1'] = 'new-value'
            with tested.bulk_update():
                tested.full['val1']['PropEl'] = 'new-prop-value'
            tested['val2'] = 'new-value-2'

        assert unordered_equal(
            setter.call_args[0][0],
            [
                {'KeyEl': 'val1', 'ValEl': 'new-value', 'PropEl': 'new-prop-value'},
                {'KeyEl': 'val2', 'ValEl': 'new-value-2', 'PropEl': 'TestAwsDict-prop2'},
            ]
        )

    def test_cache_purge_cb_on_update(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        on_purge = mock.MagicMock()
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter, setter, deleter, on_purge)

        tested['update_1.0'] = 'build_update_ctx1'
        assert on_purge.called

    def test_cache_purge_cb_on_delete(self):
        setter = mock.MagicMock()
        deleter = mock.MagicMock()
        on_purge = mock.MagicMock()
        tested = aws_dict.AwsDict('KeyEl', 'ValEl', self.default_getter, setter, deleter, on_purge)

        tested.pop('val2')
        assert on_purge.called
