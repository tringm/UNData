import json
import logging
import asyncio
import requests
from aiohttp import ClientSession
from config import set_up_logger, LOG_MAX_STR_LEN
from typing import List, Any


class Client:
    def __init__(self, base_url='http://data.un.org/ws/rest'):
        self.base_url = base_url
        self.log_file = set_up_logger()
        self.logger = logging.getLogger("Client")
        self.default_headers = {'Accept': 'text/json'}
        self.default_data_type = 'json'

    def request(self, request_method: str, path: str, data=None, data_type=None, headers=None):
        """
        Request and retun json content
        :param request_method: GET, POST, PUT, DELETE
        :param path: specific path. E.g: 'dataflow'
        :param data: body message
        :param data_type: body message type. if not declared use the default data_type
        :param headers: headers. if not declared se the default headers
        :return: request result as json
        """
        logger = self.logger

        if not headers:
            headers = self.default_headers
        if not data_type:
            data_type = self.default_data_type

        full_url = self.base_url + path
        logger.info(f"{request_method} to {path} with {data_type} data {data}")
        try:
            req_params = {'headers': headers}
            if data:
                req_params['data'] = {data_type: data}

            r = requests.request(request_method, full_url, **req_params)
            r.raise_for_status()
        except TypeError as e:
            logger.error(f"Data {data} is not in json format")
            raise e
        except requests.exceptions.HTTPError as err_h:
            logger.error(f"HTTPError: {err_h} {r.content}")
            raise err_h
        except requests.exceptions.ConnectionError as err_c:
            logger.error(f"ConnectionError: {err_c} {r.content}")
            raise err_c
        except requests.exceptions.Timeout as err_t:
            logger.error(f"Timeout: {err_t} {r.content}")
            raise err_t
        except requests.exceptions.RequestException as err:
            logger.error(f"Some error: {err} {r.content}")
            raise err
        logger.info(f"Return: {r.content[:LOG_MAX_STR_LEN]}...")
        return r.content

    def async_same_request(self, n_request, request_method, path, data=None, data_type=None, headers=None):
        """
        Async multiple same requests
        :param n_request:  number of same requests to be executed
        :param request_method: GET, POST, PUT, DELETE
        :param path: specific path
        :param data: body message
        :param data_type: body message type. if not declared use the default data_type
        :param headers: headers. if not declared se the default headers
        :return:
        """
        logger = self.logger

        if not headers:
            headers = self.default_headers
        if not data_type:
            data_type = self.default_data_type

        full_url = self.base_url + path
        logger.info(f"Async {n_request} {request_method} to {path} with {data_type} data {data}")

        req_params = {'method': request_method, 'url': full_url, 'headers': headers}
        if data:
            req_params['data'] = {data_type: data}

        async def fetch(session):
            async with session.request(**req_params) as resp:
                return await resp.text()

        async def run():
            async with ClientSession() as session:
                tasks = [fetch(session)] * n_request
                return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(run())

        logger.info(f"Return {len(responses)} responses with first response {responses[0][:LOG_MAX_STR_LEN]}...")
        return responses

    def async_request(self, request_methods: List[str], paths: List[str], data: List[Any], data_types=None,
                      headers=None):
        """
        Async requests
        :param request_methods: list of request method
        :param paths: list of request path
        :param data: list of body message
        :param data_types: body message type. if not declared use the default data_type
        :param headers: headers. if not declared se the default headers
        :return:
        """
        logger = self.logger

        if not headers:
            headers = [self.default_headers] * len(request_methods)
        if not data_types:
            data_types = [self.default_data_type] * len(request_methods)

        if not (len(request_methods) == len(paths) == len(data) == len(data_types) == len(headers)):
            raise ValueError(f"All parameters must be a list of equal length")

        async def fetch(session, req_method, url, d, h):
            async with session.request(method=req_method, url=url, data=d, headers=h) as response:
                res_json = await response.json()
                return res_json

        async def run():
            async with ClientSession() as session:
                tasks = [fetch(session, request_methods[i], full_urls[i], {data_types[i]: data[i]}, headers[i])
                         for i in range(len(request_methods))]
                return await asyncio.gather(*tasks)

        full_urls = [self.base_url + p for p in paths]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(run())

        return responses

    def get_all_flow(self):
        """
        Return json parsed data flows information
        :return:
        """
        return json.loads(self.request('GET', '/dataflow').decode('utf-8-sig'))
