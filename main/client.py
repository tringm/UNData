import json
import logging
import asyncio
import requests
from aiohttp import ClientSession
from config import set_up_logger


class Client:
    def __init__(self, base_url='http://data.un.org/ws/rest'):
        self.base_url = base_url
        self.log_file = set_up_logger()
        self.logger = logging.getLogger("Client")

    def request(self, request_method, path, data=None, data_type='json', headers=None):
        """
        Request and retun json content
        :param request_method: GET, POST, PUT, DELETE
        :param path: specific path. E.g: 'dataflow'
        :param data: body message
        :param data_type: body type. If not json, data is transformed as dictionary {data_type: data}
        :return: request result as json
        """
        logger = self.logger
        allowed_request_types = \
            {'PUT': requests.put, 'POST': requests.post, 'GET': requests.get, 'DELETE': requests.delete}

        if not headers:
            headers = {'Accept': 'text/json'}

        full_path = self.base_url + path
        logger.info(f"{request_method} to {full_path} with {data_type} data {data} headers {headers}")
        try:
            req_params = {'headers': headers}
            if data:
                if data_type == 'json':
                    req_params['json'] = data
                else:
                    req_params['data'] = {data_type: data}

            r = requests.request(request_method, full_path, **req_params)
            r.raise_for_status()
        except TypeError as e:
            logger.error(f"Data {data} is not in json format")
            raise e
        except requests.exceptions.HTTPError as err_h:
            error_message = json.loads(r.content)['error']
            logger.error(f"HTTPError: {err_h} {error_message}")
            raise err_h
        except requests.exceptions.ConnectionError as err_c:
            error_message = json.loads(r.content)['error']
            logger.error(f"ConnectionError: {err_c} {error_message}")
            raise err_c
        except requests.exceptions.Timeout as err_t:
            error_message = json.loads(r.content)['error']
            logger.error(f"Timeout: {err_t} {error_message}")
            raise err_t
        except requests.exceptions.RequestException as err:
            error_message = json.loads(r.content)['error']
            logger.error(f"Some error: {err} {error_message}")
            raise err
        return json.loads(r.content.decode('utf-8-sig'))

    def async_same_request(self, n_request, request_method, path, data=None, data_type='json', headers=None):
        """
        Async multiple same requests
        :param n_request:  number of same requests to be executed
        :param request_method: GET, POST, PUT, DELETE
        :param path: specific path
        :param data: body message
        :param data_type: body type
        :param headers: headers if needed
        :return:
        """
        logger = self.logger

        async def fetch(session, req_method, url):
            req_params = {'method': req_method, 'url': url}
            if data:
                if data_type == 'json':
                    req_params['json'] = data
                else:
                    req_params['data'] = {data_type: data}

            if not headers:
                headers = {'Accept': 'text/json'}
            req_params['headers'] = headers

            async with session.request(**req_params) as response:
                res_json = await response.json()
                return res_json

        async def run():
            async with ClientSession() as session:
                tasks = [fetch(session, request_method, full_url, data)] * n_request
                return await asyncio.gather(*tasks)

        full_url = self.url + path
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(run())
        return responses

    def async_request(self, request_methods: [str], paths: [str], data: [], use_rw_key=False):
        async def fetch(session, req_method, url, d):
            if isinstance(d, str):
                d = json.loads(d)
            logger.info(f"{req_method} to url {url}")
            async with session.request(method=req_method, url=url, json=d, headers=headers) as response:
                res_json = await response.json()
                return res_json

        async def run():
            async with ClientSession() as session:
                tasks = [fetch(session, request_methods[i], full_paths[i], data[i])
                         for i in range(len(request_methods))]
                return await asyncio.gather(*tasks)

        logger = self.logger

        headers = self.build_headers(use_rw_key)
        full_paths = [self.url + p for p in paths]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(run())
        return responses

    def get_available_data(self):
        """

        :return:
        """
        return self.request('GET', '/dataflow')
    #

    #
    # def delete_all(self):
    #     return self.request('DELETE', '/api/v1/schema', use_rw_key=True)
    #
    # def put_schema(self, schema):
    #     return self.request('PUT', '/api/v1/schema', use_rw_key=True, data=schema)
    #
    # def get_schema(self):
    #     return self.request('GET', '/api/v1/schema', use_rw_key=True)
    #
    # def populate_table_entries(self, table_name, entries):
    #     return self.request('POST', f"/api/v1/data/{table_name}/batch", use_rw_key=True, data=entries)