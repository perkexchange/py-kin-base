"""Contains the horizon api abstraction"""

import asyncio
from functools import wraps

import aiohttp
from yarl import URL

#from sseclient import SSEClient  TODO: Async sse client

from .version import __version__
from .asset import Asset
from .exceptions import HorizonError, HorizonRequestError

import logging

logger = logging.getLogger('horizon')


HORIZON_LIVE = "https://horizon.kinfederation.com"
HORIZON_TEST = "https://horizon-testnet.kininfrastructure.com"
DEFAULT_REQUEST_TIMEOUT = 11  # two ledgers + 1 sec, let's retry faster and not wait 60 secs.
DEFAULT_NUM_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
USER_AGENT = 'py-kin-base-{}'.format(__version__)


def _retry(func):
    """Retry the function on specific errors"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        self = args[0]
        for i in range(self.num_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if i == self.num_retries:
                    raise
                elif isinstance(e, (aiohttp.ClientConnectionError, aiohttp.ContentTypeError)):
                    # We couldn't connect to horizon, or the response was not a valid json (not an horizon response)
                    pass
                else:
                    raise
                logger.debug('# Retry {}: {}'.format(func.__name__, i))
                await asyncio.sleep(self.backoff_factor * i)

    return wrapper


class Horizon(object):
    def __init__(self,
                 horizon_uri=None,
                 pool_size=None,
                 num_retries=DEFAULT_NUM_RETRIES,
                 request_timeout=DEFAULT_REQUEST_TIMEOUT,
                 backoff_factor=DEFAULT_BACKOFF_FACTOR,
                 user_agent=USER_AGENT):
        """The :class:`Horizon` object, which represents the interface for
        making requests to a Horizon server instance.

        This class aims to be up to date with Horizon's API endpoints; however,
        you can utilize the internal session via ``self.session`` (which is a
        :class:`requests.Session` object) to make arbitrary requests to
        a Horizon instance's API.

        In general, on HTTP errors (non 2XX/3XX responses), no exception is
        raised, and the return dictionary must be checked to see if it is an
        error or a valid response. Any other errors however are raised by this
        class.

        :param str horizon_uri: The horizon base URL
        :param int request_timeout: The timeout for all requests.
        :param int pool_size: persistent connection to Horizon and connection pool
        :param int num_retries: configurable request retry functionality
        :param float backoff_factor: a backoff factor to apply between attempts after the second try
        :param str user_agent: String representing the user-agent you want, such as "py-stellar-base"

        """
        if horizon_uri is None:
            self.horizon_uri = URL(HORIZON_TEST)
        else:
            self.horizon_uri = URL(horizon_uri)

        self.num_retries = num_retries
        self.backoff_factor = backoff_factor

        # init session
        if pool_size is None:
            connector = aiohttp.TCPConnector()
        else:
            connector = aiohttp.TCPConnector(limit=pool_size)
        session = aiohttp.ClientSession(headers={'User-Agent': user_agent,
                                                 'Content-Type': 'application/x-www-form-urlencoded'},
                                        connector=connector,
                                        timeout=aiohttp.ClientTimeout(total=request_timeout))

        self._session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @_retry
    async def submit(self, te):
        """Submit the transaction using a pooled connection, and retry on failure.

        `POST /transactions
        <https://www.stellar.org/developers/horizon/reference/endpoints/transactions-create.html>`_

        Uses form-encoded data to send over to Horizon.

        :return: The JSON response indicating the success/failure of the
            submitted transaction.
        :rtype: dict

        """
        params = {'tx': te}
        abs_url = self.horizon_uri.join(URL('/transactions'))
        try:
            reply = await self._post(abs_url, params)
        except (aiohttp.ClientConnectionError, aiohttp.ContentTypeError) as e:
                raise HorizonRequestError(e)

        return check_horizon_reply(reply)

    async def query(self, rel_url, params=None, sse=False):
        """
        Send a query to horizon
        :param rel_url: The relative path
        :param params: Parameters to include in the query
        :param sse: Should SSE be used
        :return: The response from horizon
        """
        abs_url = self.horizon_uri.join(rel_url)
        try:
            reply = await self._get(abs_url, params, sse=sse)
        except (aiohttp.ClientConnectionError, aiohttp.ContentTypeError) as e:
                raise HorizonRequestError(e)

        return check_horizon_reply(reply) if not sse else reply

    @_retry
    async def _get(self, url, params=None, sse=False):
        """
        Send a get request
        :param url: The url to send a request to
        :param params: Parameters to include in the request
        :param sse: Should SSE be used
        :return: The response from the http request
        """
        if not sse:
            async with self._session.get(url, params=params) as response:
                return await response.json(encoding='utf-8')
        return SSEClient()  # TODO: sse client

    @_retry
    async def _post(self, url, params=None):
        """
        Send a post request
        :param url: The url to send a request to
        :param params: Parameters to include
        :return: The response from the http request
        """
        async with self._session.post(url, params=params) as response:
            return await response.json(encoding='utf-8')

    async def account(self, address):
        """Returns information and links relating to a single account.

        `GET /accounts/{account}
        <https://www.stellar.org/developers/horizon/reference/endpoints/accounts-single.html>`_

        :param str address: The account ID to retrieve details about.
        :return: The account details in a JSON response.
        :rtype: dict

        """
        endpoint = URL('/accounts/{account_id}'.format(account_id=address))
        return await self.query(endpoint)

    async def account_data(self, address, key):
        """This endpoint represents a single data associated with a given
        account.

        `GET /accounts/{account}/data/{key}
        <https://www.stellar.org/developers/horizon/reference/endpoints/data-for-account.html>`_

        :param str address: The account ID to look up a data item from.
        :param str key: The name of the key for the data item in question.
        :return: The value of the data field for the given account and data key.
        :rtype: dict

        """
        endpoint = URL('/accounts/{account_id}/data/{data_key}'.format(
            account_id=address, data_key=key))
        return await self.query(endpoint)

    async def account_effects(self, address, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all effects that changed a given account.

        `GET /accounts/{account}/effects{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/effects-for-account.html>`_

        :param str address: The account ID to look up effects for.
        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of effects in a JSON response.
        :rtype: dict

        """
        endpoint = URL('/accounts/{account_id}/effects'.format(account_id=address))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def account_offers(self, address, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all the offers a particular account makes.

        `GET /accounts/{account}/offers{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/offers-for-account.html>`_

        :param str address: The account ID to retrieve offers from.
        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of offers for an account in a JSON response.
        :rtype: dict

        """
        endpoint = URL('/accounts/{account_id}/offers'.format(account_id=address))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def account_operations(self, address, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all operations that were included in valid
        transactions that affected a particular account.

        `GET /accounts/{account}/operations{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/operations-for-account.html>`_

        :param str address: The account ID to list operations on.
        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of operations for an account in a JSON response.
        :rtype: dict

        """
        endpoint = URL('/accounts/{account_id}/operations'.format(
            account_id=address))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def account_transactions(self, address, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all transactions that affected a given
        account.

        `GET /accounts/{account_id}/transactions{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/transactions-for-account.html>`_

        :param str address: The account ID to list transactions from.
        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of transactions for an account in a JSON response.
        :rtype: dict

        """
        endpoint = URL('/accounts/{account_id}/transactions'.format(
            account_id=address))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)

        return await self.query(endpoint, params, sse)

    async def account_payments(self, address, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint responds with a collection of Payment operations where
        the given account was either the sender or receiver.

        `GET /accounts/{id}/payments{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/payments-for-account.html>`_

        :param str address: The account ID to list payments to/from.
        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of payments for an account in a JSON response.
        :rtype: dict
        """
        endpoint = URL('/accounts/{account_id}/payments'.format(account_id=address))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def account_trades(self, address, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint responds with a collection of Trades where
        the given account was either the taker or the maker

        `GET /accounts/{id}/trades{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/trades-for-account.html>`_

        :param str address: The account ID to list trades to/from.
        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of payments for an account in a JSON response.
        :rtype: dict
        """
        endpoint = URL('/accounts/{account_id}/trades'.format(account_id=address))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def assets(self, asset_code=None, asset_issuer=None, cursor=None, order='asc', limit=10):
        """This endpoint represents all assets. It will give you all the assets
        in the system along with various statistics about each.

        See the documentation below for details on query parameters that are
        available.

        `GET /assets{?asset_code,asset_issuer,cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/assets-all.html>`_

        :param str asset_code: Code of the Asset to filter by.
        :param str asset_issuer: Issuer of the Asset to filter by.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc",
            ordered by asset_code then by asset_issuer.
        :param int limit: Maximum number of records to return.

        :return: A list of all valid payment operations
        :rtype: dict

        """
        endpoint = URL('/assets')
        params = self.__query_params(asset_code=asset_code, asset_issuer=asset_issuer, cursor=cursor, order=order,
                                     limit=limit)
        return await self.query(endpoint, params)

    async def transactions(self, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all validated transactions.

        `GET /transactions{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/transactions-all.html>`_

        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: The list of all transactions
        :rtype: dict

        """
        endpoint = URL('/transactions')
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def transaction(self, tx_hash):
        """The transaction details endpoint provides information on a single
        transaction.

        `GET /transactions/{hash}
        <https://www.stellar.org/developers/horizon/reference/endpoints/transactions-single.html>`_

        :param str tx_hash: The hex-encoded transaction hash.
        :return: A single transaction's details.
        :rtype: dict

        """
        endpoint = URL('/transactions/{tx_hash}'.format(tx_hash=tx_hash))
        return await self.query(endpoint)

    async def transaction_operations(self, tx_hash, cursor=None, order='asc', limit=10):
        """This endpoint represents all operations that are part of a given
        transaction.

        `GET /transactions/{hash}/operations{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/operations-for-transaction.html>`_

        :param str tx_hash: The hex-encoded transaction hash.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A single transaction's operations.
        :rtype: dict

        """
        endpoint = URL('/transactions/{tx_hash}/operations'.format(tx_hash=tx_hash))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def transaction_effects(self, tx_hash, cursor=None, order='asc', limit=10):
        """This endpoint represents all effects that occurred as a result of a
        given transaction.

        `GET /transactions/{hash}/effects{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/effects-for-transaction.html>`_

        :param str tx_hash: The hex-encoded transaction hash.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A single transaction's effects.
        :rtype: dict

        """
        endpoint = URL('/transactions/{tx_hash}/effects'.format(tx_hash=tx_hash))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def transaction_payments(self, tx_hash, cursor=None, order='asc', limit=10):
        """This endpoint represents all payment operations that are part of a
        given transaction.

        `GET /transactions/{hash}/payments{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/payments-for-transaction.html>`_

        :param str tx_hash: The hex-encoded transaction hash.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A single transaction's payment operations.
        :rtype: dict

        """
        endpoint = URL('/transactions/{tx_hash}/payments'.format(tx_hash=tx_hash))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def order_book(self, selling_asset_code, buying_asset_code, selling_asset_issuer=None, buying_asset_issuer=None,
                   limit=10):
        """Return, for each orderbook, a summary of the orderbook and the bids
        and asks associated with that orderbook.

        See the external docs below for information on the arguments required.

        `GET /order_book
        <https://www.stellar.org/developers/horizon/reference/endpoints/orderbook-details.html>`_

        :param str selling_asset_code: Code of the Asset being sold.
        :param str buying_asset_code: Type of the Asset being bought.
        :param str selling_asset_issuer: Account ID of the issuer of the Asset being sold,
            if it is a native asset, let it be `None`.
        :param str buying_asset_issuer: Account ID of the issuer of the Asset being bought,
            if it is a native asset, let it be `None`.
        :param int limit: Limit the number of items returned.
        :return: A list of orderbook summaries as a JSON object.
        :rtype: dict

        """
        selling_asset = Asset(selling_asset_code, selling_asset_issuer)
        buying_asset = Asset(buying_asset_code, buying_asset_issuer)
        asset_params = {
            'selling_asset_type': selling_asset.type,
            'selling_asset_code': None if selling_asset.is_native() else selling_asset.code,
            'selling_asset_issuer': selling_asset.issuer,
            'buying_asset_type': buying_asset.type,
            'buying_asset_code': None if buying_asset.is_native() else buying_asset.code,
            'buying_asset_issuer': buying_asset.issuer,
        }
        endpoint = URL('/order_book')
        params = self.__query_params(limit=limit, **asset_params)
        return await self.query(endpoint, params)

    async def ledgers(self, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all ledgers.

        `GET /ledgers{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/ledgers-all.html>`_

        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: All ledgers on the network.
        :rtype: dict

        """
        endpoint = URL('/ledgers')
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def ledger(self, ledger_id):
        """The ledger details endpoint provides information on a single ledger.

        `GET /ledgers/{sequence}
        <https://www.stellar.org/developers/horizon/reference/endpoints/ledgers-single.html>`_

        :param int ledger_id: The id of the ledger to look up.
        :return: The details of a single ledger.
        :rtype: dict

        """
        endpoint = URL('/ledgers/{ledger_id}'.format(ledger_id=ledger_id))
        return await self.query(endpoint)

    async def ledger_transactions(self, ledger_id, cursor=None, order='asc', limit=10):
        """This endpoint represents all transactions that occurred in the given
        ledger.

        `GET /ledgers/{id}/transactions{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/effects-for-ledger.html>`_

        :param int ledger_id: The id of the ledger to look up.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: The transactions for a single ledger.
        :rtype: dict

        """
        endpoint = URL('/ledgers/{ledger_id}/transactions'.format(ledger_id=ledger_id))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def ledger_effects(self, ledger_id, cursor=None, order='asc', limit=10):
        """This endpoint represents all effects that occurred in the given
        ledger.

        `GET /ledgers/{id}/effects{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/effects-for-ledger.html>`_

        :param int ledger_id: The id of the ledger to look up.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: The effects for a single ledger.
        :rtype: dict

        """
        endpoint = URL('/ledgers/{ledger_id}/effects'.format(ledger_id=ledger_id))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def ledger_operations(self, ledger_id, cursor=None, order='asc', limit=10):
        """This endpoint returns all operations that occurred in a given
        ledger.

        `GET /ledgers/{id}/operations{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/operations-for-ledger.html>`_

        :param int ledger_id: The id of the ledger to look up.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: The operations contained in a single ledger.
        :rtype: dict

        """
        endpoint = URL('/ledgers/{ledger_id}/operations'.format(
            ledger_id=ledger_id))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def ledger_payments(self, ledger_id, cursor=None, order='asc', limit=10):
        """This endpoint represents all payment operations that are part of a
        valid transactions in a given ledger.

        `GET /ledgers/{id}/payments{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/payments-for-ledger.html>`_

        :param int ledger_id: The id of the ledger to look up.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: The payments contained in a single ledger.
        :rtype: dict

        """
        endpoint = URL('/ledgers/{ledger_id}/payments'.format(ledger_id=ledger_id))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def effects(self, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all effects.

        `GET /effects{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/effects-all.html>`_

        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: A list of all effects.
        :rtype: dict

        """
        endpoint = URL('/effects')
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def operations(self, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all operations that are part of validated
        transactions.

        `GET /operations{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/operations-all.html>`_

        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: A list of all operations.
        :rtype: dict

        """
        endpoint = URL('/operations')
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def operation(self, op_id):
        """The operation details endpoint provides information on a single
        operation.

        `GET /operations/{id}
        <https://www.stellar.org/developers/horizon/reference/endpoints/operations-single.html>`_

        :param id op_id: The operation ID to get details on.
        :return: Details on a single operation.
        :rtype: dict
        """
        endpoint = URL('/operations/{op_id}'.format(op_id=op_id))
        return await self.query(endpoint)

    async def operation_effects(self, op_id, cursor=None, order='asc', limit=10):
        """This endpoint represents all effects that occurred as a result of a
        given operation.

        `GET /operations/{id}/effects{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/effects-for-operation.html>`_

        :param int op_id: The operation ID to get effects on.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A list of effects on the given operation.
        :rtype: dict

        """
        endpoint = URL('/operations/{op_id}/effects'.format(op_id=op_id))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def payments(self, cursor=None, order='asc', limit=10, sse=False):
        """This endpoint represents all payment operations that are part of
        validated transactions.

        `GET /payments{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/payments-all.html>`_

        :param cursor: A paging token, specifying where to start returning records from.
            When streaming this can be set to "now" to stream object created since your request time.
        :type cursor: int, str
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :param bool sse: Use server side events for streaming responses.
        :return: A list of all valid payment operations.
        :rtype: dict

        """
        endpoint = URL('/payments')
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params, sse)

    async def paths(self, destination_account, destination_amount, source_account, destination_asset_code,
              destination_asset_issuer=None):
        """Load a list of assets available to the source account id and find
        any payment paths from those source assets to the desired
        destination asset.

        See the below docs for more information on required and optional
        parameters for further specifying your search.

        `GET /paths
        <https://www.stellar.org/developers/horizon/reference/endpoints/path-finding.html>`_

        :param str destination_account: The destination account that any returned path should use.
        :param str destination_amount: The amount, denominated in the destination asset,
            that any returned path should be able to satisfy.
        :param str source_account: The sender's account id. Any returned path must use a source that the sender can hold.
        :param str destination_asset_code: The asset code for the destination.
        :param destination_asset_issuer: The asset issuer for the destination, if it is a native asset, let it be `None`.
        :type destination_asset_issuer: str, None


        :return: A list of paths that can be used to complete a payment based
            on a given query.
        :rtype: dict

        """
        destination_asset = Asset(destination_asset_code, destination_asset_issuer)
        destination_asset_params = {
            'destination_asset_type': destination_asset.type,
            'destination_asset_code': None if destination_asset.is_native() else destination_asset.code,
            'destination_asset_issuer': destination_asset.issuer
        }
        endpoint = URL('/paths')
        params = self.__query_params(destination_account=destination_account,
                                     source_account=source_account,
                                     destination_amount=destination_amount,
                                     **destination_asset_params
                                     )
        return await self.query(endpoint, params)

    async def trades(self, base_asset_code=None, counter_asset_code=None, base_asset_issuer=None, counter_asset_issuer=None,
               offer_id=None, cursor=None, order='asc', limit=10):
        """Load a list of trades, optionally filtered by an orderbook.

        See the below docs for more information on required and optional
        parameters for further specifying your search.

        `GET /trades
        <https://www.stellar.org/developers/horizon/reference/endpoints/trades.html>`_

        :param str base_asset_code: Code of base asset.
        :param str base_asset_issuer: Issuer of base asset, if it is a native asset, let it be `None`.
        :param str counter_asset_code: Code of counter asset.
        :param str counter_asset_issuer: Issuer of counter asset, if it is a native asset, let it be `None`.
        :param int offer_id: Filter for by a specific offer id.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A list of trades filtered by a given query.
        :rtype: dict

        """
        base_asset = Asset(base_asset_code, base_asset_issuer)
        counter_asset = Asset(counter_asset_code, counter_asset_issuer)
        asset_params = {
            'base_asset_type': base_asset.type,
            'base_asset_code': None if base_asset.is_native() else base_asset.code,
            'base_asset_issuer': base_asset.issuer,
            'counter_asset_type': counter_asset.type,
            'counter_asset_code': None if counter_asset.is_native() else counter_asset.code,
            'counter_asset_issuer': counter_asset.issuer
        }
        endpoint = URL('/trades')
        params = self.__query_params(offer_id=offer_id, cursor=cursor, order=order, limit=limit, **asset_params)
        return await self.query(endpoint, params)

    async def trade_aggregations(self, resolution, base_asset_code, counter_asset_code,
                           base_asset_issuer=None, start_time=None, end_time=None,
                           counter_asset_issuer=None, order='asc', limit=10):
        """Load a list of aggregated historical trade data, optionally filtered
        by an orderbook.

        `GET /trade_aggregations
        <https://www.stellar.org/developers/horizon/reference/endpoints/trade_aggregations.html>`_

        :param int start_time: Lower time boundary represented as millis since epoch.
        :param int end_time: Upper time boundary represented as millis since epoch.
        :param int resolution: Segment duration as millis since epoch. Supported values
            are 1 minute (60000), 5 minutes (300000), 15 minutes (900000), 1 hour (3600000),
            1 day (86400000) and 1 week (604800000).
        :param str base_asset_code: Code of base asset.
        :param str base_asset_issuer: Issuer of base asset, if it is a native asset, let it be `None`.
        :param str counter_asset_code: Code of counter asset.
        :param str counter_asset_issuer: Issuer of counter asset, if it is a native asset, let it be `None`.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A list of collected trade aggregations.
        :rtype: dict

        """
        base_asset = Asset(base_asset_code, base_asset_issuer)
        counter_asset = Asset(counter_asset_code, counter_asset_issuer)
        asset_params = {
            'base_asset_type': base_asset.type,
            'base_asset_code': None if base_asset.is_native() else base_asset.code,
            'base_asset_issuer': base_asset.issuer,
            'counter_asset_type': counter_asset.type,
            'counter_asset_code': None if counter_asset.is_native() else counter_asset.code,
            'counter_asset_issuer': counter_asset.issuer
        }
        endpoint = URL('/trade_aggregations')
        params = self.__query_params(start_time=start_time, end_time=end_time, resolution=resolution, order=order,
                                     limit=limit, **asset_params)
        return await self.query(endpoint, params)

    async def offer_trades(self, offer_id, cursor=None, order='asc', limit=10):
        """This endpoint represents all trades for a given offer.

        `GET /offers/{offer_id}/trades{?cursor,limit,order}
        <https://www.stellar.org/developers/horizon/reference/endpoints/trades-for-offer.html>`_

        :param int offer_id: The offer ID to get trades on.
        :param int cursor: A paging token, specifying where to start returning records from.
        :param str order: The order in which to return rows, "asc" or "desc".
        :param int limit: Maximum number of records to return.
        :return: A list of effects on the given operation.
        :rtype: dict

        """
        endpoint = URL('/offers/{offer_id}/trades'.format(offer_id=offer_id))
        params = self.__query_params(cursor=cursor, order=order, limit=limit)
        return await self.query(endpoint, params)

    async def metrics(self):
        """The metrics endpoint returns a host of useful data points for monitoring the health
        of the underlying Horizon process.

        `GET /metrics
        <https://www.stellar.org/developers/horizon/reference/endpoints/metrics.html>`_

        :return: A host of useful data points for monitoring the health of the underlying Horizon process
        :rtype: dict
        """

        endpoint = URL('/metrics')
        return await self.query(endpoint)

    @staticmethod
    async def __query_params(**kwargs):
        params = {k: v for k, v in kwargs.items() if v is not None}
        return params

    async def close(self):
        """Close the connection to horizon"""
        await self._session.__aexit__(None, None, None)


def check_horizon_reply(reply):
    if 'status' not in reply:
        return reply
    raise HorizonError(reply)


async def horizon_testnet():
    """Create a Horizon instance utilizing Kin's Test Network."""
    return Horizon(HORIZON_TEST)


async def horizon_livenet():
    """Create a Horizon instance utilizing Kin's Live Network."""
    return Horizon(HORIZON_LIVE)
