import hashlib
from enum import Enum
from typing import List, Union

import aiohttp

from api_types import Transaction, AccountInfo

TRANSACTIONS_HISTORY_ENDPOINT = 'https://merchant.betatransfer.io/api/history'
ACCOUNT_INFO_ENDPOINT = 'https://merchant.betatransfer.io/api/account-info'


class TransTypes(Enum):
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'


class StatusCodes(Enum):
    SUCCESS = 'success'
    PROCESSING = 'processing'
    ERROR = 'error'
    CANCEL = 'cancel'


class API:
    def __init__(self, api_token_public, api_token_private):
        self.__session = aiohttp.ClientSession()

        self._api_token_public = api_token_public
        self._api_token_private = api_token_private

    async def __generate_sing(self, params: List):
        params = [str(param) for param in params]
        if params:
            params = ''.join(params)
            params += self._api_token_private
        else:
            params = self._api_token_private
        sign = hashlib.md5(params.encode())
        return sign.hexdigest()

    async def get_account_info(self) -> AccountInfo:
        endpoint = ACCOUNT_INFO_ENDPOINT

        sign_params = [self._api_token_public]
        sign = await self.__generate_sing(sign_params)

        params = {
            'token': self._api_token_public,
            'sign': sign
        }

        response = await self.__session.get(endpoint, params=params)
        response_json = await response.json()
        return AccountInfo(
            balance_rub=response_json['balance']['RUB'],
            balance_usd=response_json['balance']['USD'],
            balance_uah=response_json['balance']['UAH'],
            balance_on_hold_rub=response_json['balance_on_hold']['RUB'],
            balance_on_hold_usd=response_json['balance_on_hold']['USD'],
            balance_on_hold_uah=response_json['balance_on_hold']['UAH'],
            lock_withdrawal=response_json['account']['lockWithdrawal'],
            lock_account=response_json['account']['lockAccount']
        )

    async def get_transactions_history(self, limit: int = None,
                                       t_type: Union[str, TransTypes] = None,
                                       status: Union[str, StatusCodes] = None,
                                       address: str = None) -> List[Transaction]:
        endpoint = TRANSACTIONS_HISTORY_ENDPOINT

        if isinstance(status, StatusCodes):
            status = status.value

        if isinstance(t_type, TransTypes):
            t_type = t_type.value

        params = {'token': self._api_token_public}

        sign_params = []
        sign_params.append(t_type) if t_type else None
        sign_params.append(limit) if limit else None
        sign_params.append(status) if status else None
        sign_params.append(address) if address else None
        sign = await self.__generate_sing(sign_params)

        data = {}
        data.update({'type': t_type}) if t_type else None
        data.update({'limit': limit}) if limit else None
        data.update({'status': status}) if status else None
        data.update({'address': address}) if address else None
        data.update({'sign': sign}) if sign else None

        response = await self.__session.post(endpoint, params=params, data=data)
        result = []
        response_json = await response.json()
        for item in response_json['items']:
            result.append(Transaction(
                id=int(item['id']),
                type=item['type'],
                amount=float(item['amount']),
                payment_system=item['paymentSystem'],
                currency=item['currency'],
                address=item['address'],
                payment_card=item['paymentCard'],
                status=item['status']
            ))
        return result
