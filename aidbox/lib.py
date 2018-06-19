import json
import requests
import inflection

from urllib.parse import parse_qsl

from .utils import convert_to_underscore
from .exceptions import AidboxResourceFieldDoesNotExist, AidboxResourceNotFound


class Aidbox:
    def __init__(self, host, email, password):
        r = requests.post(
            '{0}/oauth2/authorize'.format(host),
            params={
                'client_id': 'sansara',
                'scope': 'openid profile email',
                'response_type': 'id_token',
            },
            data={'email': email, 'password': password},
            allow_redirects=False
        )
        token_data = dict(parse_qsl(r.headers['location']))

        self.host = host
        self.token = token_data['id_token']

    def resource(self, resource_type, **kwargs):
        kwargs['resource_type'] = resource_type
        return AidboxResource(self, **kwargs)

    def resources(self, resource_type):
        return AidboxSearchSet(self, resource_type=resource_type)
    # TODO: define __str__, __repr__

    def _fetch_resource(self, path):
        r = requests.get(
            '{0}/{1}'.format(self.host, path),
            headers={'Authorization': 'Bearer {0}'.format(self.token)})
        if r.status_code == 404:
            raise AidboxResourceNotFound()

        result = json.loads(r.text)
        return convert_to_underscore(result)

    def _fetch_root_attrs(self, resource_type):
        attrs_data = self._fetch_resource(
            'Attribute?entity={0}'.format(resource_type))
        attrs = [res['resource'] for res in attrs_data['entry']]
        return {inflection.underscore(attr['path'][0]) for attr in attrs}


class AidboxSearchSet:
    aidbox = None
    resource_type = None

    def __init__(self, aidbox, resource_type):
        self.aidbox = aidbox
        self.resource_type = resource_type

    def get(self, id):
        res_data = self.aidbox._fetch_resource(
            '{0}/{1}'.format(self.resource_type, id))
        return self.aidbox.resource(**res_data)

    def all(self):
        res_data = self.aidbox._fetch_resource(self.resource_type)
        resource_data = [res['resource'] for res in res_data['entry']]
        root_attrs = self.aidbox._fetch_root_attrs(self.resource_type)
        return [AidboxResource(
            self.aidbox,
            root_attrs,
            **data
        ) for data in resource_data]

    def first(self):
        # TODO: return first item from list
        pass

    def last(self):
        # TODO: return last item from list
        # TODO: sort (-) + first
        pass

    def search(self, **kwargs):
        # TODO: use SearchParameter.name
        # TODO: fetch_resource params=kwargs
        # TODO: .filter(name='John') -> ?name=john
        pass

    def limit(self, limit):
        pass

    def offset(self, offset):
        pass

    def sort(self, keys):
        pass

    def include(self):
        # https://www.hl7.org/fhir/search.html
        # works as select_related
        # result: Bundle [patient1, patientN, clinic1, clinicN]
        # searchset.filter(name='john').get(pk=1)
        pass

    def revinclude(self):
        # https://www.hl7.org/fhir/search.html
        # works as prefetch_related
        pass

    # TODO: define __str__, __repr__


class AidboxResource:
    aidbox = None
    resource_type = None
    root_attrs = []

    data = {}
    meta = {}

    def __init__(self, aidbox, root_attrs=None, **kwargs):
        self.data = {}
        self.aidbox = aidbox
        self.resource_type = kwargs.get('resource_type')

        if not root_attrs:
            self.root_attrs = aidbox._fetch_root_attrs(self.resource_type)
        else:
            self.root_attrs = root_attrs

        meta = kwargs.pop('meta', {})
        self.meta = meta

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, key, value):
        if key in dir(self):
            super(AidboxResource, self).__setattr__(key, value)
        elif key in self.root_attrs:
            if isinstance(value, AidboxResource):
                self.data[key] = value.reference()
            else:
                self.data[key] = value
        else:
            raise AidboxResourceFieldDoesNotExist(
                'Invalid attribute `{0}` for resource `{1}`'.format(
                    key, self.resource_type))

    def __getattr__(self, key):
        if key in self.root_attrs:
            return self.data.get(key, None)
        else:
            raise AidboxResourceFieldDoesNotExist(
                'Invalid attribute `{0}` for resource `{1}`'.format(
                    key, self.resource_type))

    def save(self):
        # pass over data and when we see type(field) == AidboxReference, then
        # convert to dict with {'resource_type': '', 'id': ''}
        # then CamelCase it and post JSON to server
        pass

    def delete(self):
        pass

    def reference(self):
        return AidboxReference(self.aidbox, self.resource_type, self.id)
    # TODO: define __str__, __repr__


class AidboxReference:
    aidbox = None
    resource_type = None
    id = None

    def __init__(self, aidbox, resource_type, id, **kwargs):
        self.aidbox = aidbox
        self.resource_type = resource_type
        self.id = id
        # TODO: parse kwargs (display, resource)

    # TODO: define __str__, __repr__
