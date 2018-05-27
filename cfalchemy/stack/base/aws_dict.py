import collections
import contextlib
import threading
import logging
import six

log = logging.getLogger(__name__)


class AwsItem(collections.MutableMapping):
    """AWS item record"""

    def __init__(self, parent_aws, my_key, prop_values):
        super(AwsItem, self).__init__()
        assert isinstance(my_key, six.string_types)
        assert isinstance(prop_values, dict)
        self.data = prop_values.copy()
        self.key = my_key
        self._parent_aws = parent_aws
        self._no_propagate = 0

    def __getitem__(self, item):
        return self.data[item]

    def __delitem__(self, key):
        if self._no_propagate:
            del self.data[key]
        else:
            new_val = self.copy()
            with new_val.no_propagate():
                del new_val[key]
            self._parent_aws[self.key] = new_val

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __setitem__(self, key, value):
        if self._no_propagate:
            self.data[key] = value
        else:
            new_val = self.copy()
            with new_val.no_propagate():
                new_val[key] = value
            self._parent_aws[self.key] = new_val

    @contextlib.contextmanager
    def no_propagate(self):
        self._no_propagate += 1
        try:
            yield
        finally:
            self._no_propagate -= 1

    def copy(self):
        return self.__class__(
            self._parent_aws,
            self.key,
            self.data.copy()
        )


class AwsPropsDictComplete(collections.MutableMapping):
    """Generic aws props dict.

        Transforms list of generic {<name_key>: <value>, <value_key>: <value>, ... <extra_prop>: <value> } dict items
        to something that resemples python dict bit better.

        This object provides complete access to all extra value properties.
            'values' is an iterable of names of value items

        The object relies on getter/setter/deleter methods to read/amend/delete dict values

        'Setter' and 'Deleter' handlers are expected to accept same iterable of {} to be set/deleted.
        'Deleter' will be only provided with one-element {<key_name>: <value>} dicts.
    """

    # This object will contain:
    #  'updates' list of pending updates dicts
    #       idx 0 = top fo the stack
    dict_thread_stacks = threading.local()

    def __init__(self, key_name, getter, setter=None, deleter=None):
        assert isinstance(key_name, str)
        self.key_name = key_name
        assert callable(getter)
        self.getter = getter
        self.setter = setter
        self.deleter = deleter
        self.dict_thread_stacks.updates = []

    def set_setter(self, new_setter):
        assert callable(new_setter)
        self.setter = new_setter

    def set_deleter(self, new_deleter):
        assert callable(new_deleter)
        self.deleter = new_deleter

    def __setitem__(self, key, value):
        self.update(**{key: value})

    def __delitem__(self, key):
        self.update(**{key: None})

    def __getitem__(self, key):
        return self.current_items_view[key]

    def __len__(self):
        return len(self.current_items_view)

    def __iter__(self):
        return iter(self.current_items_view)

    def update(self, **params):
        """Update the dictionary. Updating value to 'None' causes for it to be deleted"""
        with self.bulk_update():
            aws_params = {}
            for (name, value) in params.items():
                if value is not None and not isinstance(value, AwsItem):
                    # Must be a vanilla dict for new element
                    value[self.key_name] = name
                    value = self._mk_aws_item(value)
                aws_params[name] = value
            self.dict_thread_stacks.updates[-1].update(aws_params)

    @contextlib.contextmanager
    def bulk_update(self):
        """This context syncs all scheduled updates only on exit from the last 'with' statement"""
        self.my_updates.append({})
        try:
            yield
        except:  # noqa
            # Remove my update stack
            self.my_updates.pop()
            raise
        else:
            # No exceptions
            my_update_stack = self.my_updates
            my_el = my_update_stack.pop()
            if my_update_stack:
                # There are transactions above this one
                self.my_updates[-1].update(my_el)
            else:
                self.commit_update(my_el)

    def commit_update(self, data_dict):
        to_set = []
        to_delete = []
        for (name, value) in data_dict.items():
            api_el = {self.key_name: name}
            if value is None:
                to_delete.append(api_el)
            else:
                api_el.update(value.data)
                to_set.append(api_el)
        if to_set and not self.setter:
            raise NotImplementedError('You must provide "setter" to update dict elements.')
        elif to_set:
            self.setter(to_set)

        if to_delete and not self.deleter:
            raise NotImplementedError('You must provide "delete" to delete elements')
        elif to_delete:
            self.deleter(to_delete)
        self._remote_item_cache = None  # force remote item reload

    @property
    def current_items_view(self):
        out = self.remote_items.copy()
        if self.pending_updates:
            for (name, value) in self.pending_updates.items():
                if value is None:
                    out.pop(name, None)
                else:
                    out[name] = value
        return out

    @property
    def pending_updates(self):
        out = {}
        for layer in self.my_updates:
            # Iter iterates from idx 0 (oldest) to idx -1 (newest)
            out.update(layer)
        return out

    @property
    def my_updates(self):
        try:
            return self.dict_thread_stacks.updates
        except AttributeError:
            raise KeyError('Are you trying to update an aws dict created in another thread?')

    _remote_item_cache = None

    @property
    def remote_items(self):
        if self._remote_item_cache is None:
            _remote_item_cache = {}
            for el in self.getter():
                item_el = self._mk_aws_item(el)
                _remote_item_cache[item_el.key] = item_el
            self._remote_item_cache = _remote_item_cache
        return self._remote_item_cache.copy()

    def _mk_aws_item(self, raw_data):
        data = {}
        key = None
        for (name, value) in raw_data.items():
            if name == self.key_name:
                key = value
            else:
                data[name] = value

        assert key is not None, "Key has to be present"
        return AwsItem(self, key, data)

    def __repr__(self):
        return "<{}.{} vals={}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            dict(self)
        )
