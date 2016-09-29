import json

class AppReqTestHelper(object):
    """
    Adds convenience self.post, self.get, self.put, self.delete, self.patch
    methods on the testcase object.

    Assumes a flask app client is defined on self.client
    """
    def _req(self, meth, *args, **kwargs):
        if kwargs.get('content_type') is None and meth != 'get':
            kwargs['content_type'] = 'application/json'

        if kwargs.get('json') is not None:
            kwargs['data'] = json.dumps(kwargs.get('json'))
            del kwargs['json']

        # Take provided headers or fall back.
        headers = kwargs.pop('headers', getattr(self, 'client_headers', {}))

        func = getattr(self.client, meth)
        rv = func(*args, headers=headers, **kwargs)

        def get_json():
            return json.loads(rv.data.decode('UTF-8'))

        rv.get_json = get_json
        return rv

    def post(self, *args, **kwargs):
        return self._req('post', *args, **kwargs)

    def get(self, *args, **kwargs):
        return self._req('get', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._req('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._req('delete', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._req('patch', *args, **kwargs)


class PrivilegeTestHelper(AppReqTestHelper):
    def do_test_privileges(self, endpoint, data, object_id, expected_codes):
        for meth, expected_code in expected_codes:
            assert meth in ['plural-get', 'get', 'delete', 'put', 'post']

            kwargs = {}
            endp = endpoint
            _meth = meth
            if meth in ['put', 'post']:
                kwargs['json'] = data

            if meth in ['put', 'delete', 'get']:
                endp = endpoint + '/{}'.format(object_id)

            if meth == 'plural-get':
                _meth = 'get'

            rv = self._req(_meth, endp, **kwargs)
            self.assertEqual(rv.status_code, expected_code, 
                             "Expected {} for method {} but got {}. {}".format(
                                expected_code, meth, rv.status_code, rv.get_json()))


class CRUDTestHelper(AppReqTestHelper):
    def do_crud_test(self, endpoint, data_1=None, data_2=None, key='id', 
                     check_keys=[], keys_from_prev=[], create=True, delete=True, 
                     update=True, read=True, initial_count=0):

        if read:
            # Plural read on initial set.
            rv = self.get(endpoint)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(len(rv.get_json()), initial_count)

        if create:
            # Create
            rv = self.post(endpoint, json=data_1)
            self.assertEqual(rv.status_code, 200)
            self.assertEqualDicts(check_keys, rv.get_json(), data_1)
            key_id = rv.get_json()[key]

        if read:
            # Plural read
            rv = self.get(endpoint)
            self.assertEqual(rv.status_code, 200)
            if create:
                self.assertEqual(len(rv.get_json()), initial_count + 1)
                # Ensure that at least one of the items is equal to the one we made
                for item in rv.get_json():
                    if self.equalDicts(check_keys, item, data_1):
                        break
                else: # nobreak
                    self.fail("Could not find the object that was created in the response.")

            else:
                # No object should have been created
                self.assertEqual(len(rv.get_json()), initial_count)

        if read and create:
            # Singular Read
            rv = self.get(endpoint + '/' + str(key_id))
            self.assertEqual(rv.status_code, 200)
            prev_data = rv.get_json() # Keep this data so we can use it after update.
            self.assertEqualDicts(check_keys, prev_data, data_1)

        if update and create:
            # Singular Update
            rv = self.put(endpoint + '/' + str(key_id), json=data_2)
            self.assertEqual(rv.status_code, 200)
            self.assertEqualDicts(check_keys, rv.get_json(), data_2)
            self.assertEqualDicts(keys_from_prev, rv.get_json(), prev_data)
        
        if read and create:
            # Singular Read to confirm persisted.
            rv = self.get(endpoint + '/' + str(key_id))
            self.assertEqual(rv.status_code, 200)
            self.assertEqualDicts(check_keys, rv.get_json(), data_2)
            self.assertEqualDicts(keys_from_prev, rv.get_json(), prev_data)

        if delete and create:
            # Singular Deletion
            rv = self.delete(endpoint + '/' + str(key_id))
            self.assertEqual(rv.status_code, 200)

        if read and create:
            # Singular read on object which doesn't exist.
            rv = self.get(endpoint + '/' + str(key_id))
            self.assertEqual(rv.status_code, 404)

        if read:
            # Plural read on empty set
            rv = self.get(endpoint)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(len(rv.get_json()), initial_count)

    def filteredDicts(self, keys, *dicts):
        ret = []
        for d in dicts:    
            d_filtered = dict((k, v) for k, v in d.items()
                              if k in keys)
            ret.append(d_filtered)
        
        return ret

    def assertEqualDicts(self, keys, d1, d2):
        self.assertEqual(*self.filteredDicts(keys, d1, d2))

    def equalDicts(self, keys, d1, d2):
        d1, d2 = self.filteredDicts(keys, d1, d2)
        return d1 == d2

