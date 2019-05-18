import unittest
from main.client import Client
from test.setup import GenericTestCase


class TestClient(GenericTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def test_request(self):
        self.client.request('GET', '/dataflow')

    @unittest.expectedFailure
    def test_wrong_request(self):
        self.client.request('POST', '/dataflow')

    def test_get_all_flows(self):
        res = self.client.get_all_flow()
        self.assertIn('resources', res)
        self.assertIn('references', res)
        for flow in res['resources']:
            self.assertIn('id', flow)
            self.assertIn('urn', flow)
