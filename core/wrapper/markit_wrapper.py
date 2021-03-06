#!/usr/bin/env python3


import json

import requests

from ..serializer.markit_quote_decoder import MarkitOnDemandQuoteDecoder
from ..serializer.markit_asset_decoder import MarkitOnDemandAssetDecoder


class MarkitOnDemand():
    """Wrapper for MarkitOnDemand API, version 2, expecting JSON objects as result.

    Supported API Functions:
        - Quote: Quote information about a specific ticker symbol (stock).
        - Lookup: Basic ticker information (company name, symbol name and exchange).

    Note:
        API documentation available at: http://dev.markitondemand.com/MODApis/Api/v2/doc/.

    """

    # API url and version identifiers
    URL = 'http://dev.markitondemand.com/MODApis/Api'
    VERSION = 'v2'
    # API function identifiers
    FUNCTION_QUOTE = 'quote'
    FUNCTION_LOOKUP = 'lookup'
    FUNCTION_PARAMS = {FUNCTION_QUOTE: 'symbol', FUNCTION_LOOKUP: 'input'}

    @staticmethod
    def build_endpoint(api_function, param_value):
        """Creates the url to be used for calling a specific API endpoint.

        Args:
            api_call (str): The API function to be called.
            param (str): The parameter to be passed to the API function.

        Returns:
            The complete URL needed to call the specified API function.
        """

        if api_function.lower() not in MarkitOnDemand.FUNCTION_PARAMS:
            raise ValueError('Invalid API function {}.'.format(api_function))

        # Expected API url format
        endpoint_format = '{url}/{version}/{function}/json?{param_name}={param_value}'
        return endpoint_format.format(url=MarkitOnDemand.URL,
                                      version=MarkitOnDemand.VERSION,
                                      function=api_function.lower(),
                                      param_name=MarkitOnDemand.FUNCTION_PARAMS[api_function],
                                      param_value=param_value
                                      )

    @staticmethod
    def quote(ticker_symbol):
        """Gets quote information for a specific ticker symbol.

        API function name: Quote.

        API function endpoint: http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol='ticker_symbol'.

        Args:
            ticker_symbol (str): ticker symbol to look for a quote.

        Returns:
            dictionary: quote information for a specific 'ticker_symbol', as a JSON object:
                {
                    "name": string,
                    "symbol": string,
                    "exchange": "" (Default)
                    "last_price": float,
                    "change_1h": 0.0 (Default),
                    "change_percent_1h": 0.0 (Default),
                    "change_1d": float,
                    "change_percent_1d": float,
                    "change_7d": 0.0 (Default),
                    "change_percent_7d": 0.0 (Default),
                    "change_year": float,
                    "change_percent_year": float,
                    "timestamp": string,
                    "market_cap": integer,
                    "volume": integer,
                    "high": float,
                    "low": float,
                    "open": float
                }

        Raises:
            ValueError: if 'ticker_symbol' is empty or does not correspond to a valid ticker symbol.

        """

        # Successfull API call returns a JSON object that contains a field 'Status'.
        #
        # Incorrect API Calls passing an empty/invalid parameter return a JSON object with a field 'Message'.
        # Invalid Symbol: {
        #   "Message":"No symbol matches found for tsla2.
        #   Try another symbol such as MSFT or AAPL, or use the Lookup API."
        # }
        # Missing Symbol: {
        #   "Message":"Missing Required Parameter: \"symbol\""
        # }

        if (ticker_symbol is None) or (ticker_symbol.strip() == ''):
            raise ValueError('Missing required parameter "ticker_symbol".')

        # Creates and call API endpoint, then loads result into json result object.
        endpoint = MarkitOnDemand.build_endpoint(MarkitOnDemand.FUNCTION_QUOTE,
                                                 ticker_symbol)
        result = requests.get(endpoint)
        # print(result.status_code)
        if not result.ok:
            result.raise_for_status()

        json_obj = json.loads(result.text)

        # Status must be equal to SUCCESS to be a valid Quote.
        # In case a different Status is returned from the API (unexpected),
        # due to internal errors for instance, raises an exception.
        if 'Status' in json_obj and json_obj['Status'] == 'SUCCESS':
            return json.loads(result.text, cls=MarkitOnDemandQuoteDecoder)
        elif 'Status' in json_obj:
            raise ValueError(json_obj['Status'])

        if 'Message' in json_obj:
            raise ValueError(json_obj['Message'])

        # Should not arrive to this point.
        # If it does, an unsupported JSON object was returned from the API.
        raise TypeError("""Unsupported JSON object returned. Details:
                        \nEndpoint: '{endpoint}'.
                        \nJSON Object: {json_object}.
                        """.format(endpoint=endpoint, json_object=json_obj))

    @staticmethod
    def lookup(search_input):
        """Gets lookup information for a specific 'input'.

        API function name: Lookup.

        API function endpoint: http://dev.markitondemand.com/MODApis/Api/v2/Lookup/json?input='search_input'.

        Args:
            search_input (str): input text to search for.

        Returns:
            None: if no content was found based on 'search_input'. Otherwise;
            list: a list of dictionaries with lookup data, in the following format:
            [
                {
                "Symbol":string,
                "Name":string,
                "Exchange":string
                }
                , ...
            ]

        Raises:
            ValueError: if an error message is returned from the API.

        """

        # Successfull API call returns a list of JSON objects with lookup data.
        # There is no status indication in this object, when the call is successful.
        # Incorrect API Calls passing an empty/invalid parameter return a JSON object with a field 'Message'.
        # {"Message":"Missing Required Parameter: \"input\""}
        # The API result needs to be checked for a 'Message' field, before converting
        # the result to a list of asset dictionaries.

        if (search_input is None) or (search_input.strip() == ''):
            raise ValueError('Missing required parameter "search_input".')

        # Creates and call API endpoint, then loads result into json result object.
        endpoint = MarkitOnDemand.build_endpoint(MarkitOnDemand.FUNCTION_LOOKUP,
                                                 search_input)
        result = requests.get(endpoint)
        if not result.ok:
            result.raise_for_status()

        # Checks if the API returned a message error due to an invalid parameter.
        json_obj = json.loads(result.text)
        if 'Message' in json_obj:
            raise ValueError(json_obj['Message'])

        # If no error was found, converts the JSON to a list of dictionaries.
        json_obj = json.loads(result.text, cls=MarkitOnDemandAssetDecoder)

        return json_obj if (len(json_obj) > 0) else None

    @staticmethod
    def lookup_exchange(ticker_symbol):
        """Lookups for the exchange where 'ticker_symbol' is traded.

        Args:
            ticker_symbol (str): used to identify the exchange where the 'ticker_symbol' is traded.

        Returns:
            None: if no exchange was found based on 'ticker_symbol'. Otherwise;
            string: the name of the exchange where 'ticker_symbol' is traded.
                If 'ticker_symbol' is traded in more than one exchange,
                returns the first exchange found.

        Raises:
            ValueError: if an error message is returned from the API.

        """

        # API Lookup function looks for 'input=ticker_symbol' in "symbols"
        # and in "company names". It may happen that a ticker symbol matches a
        # character sequence in a company name (not associated to the symbol).
        # Because of this, it is necessary to loop over the result and compare
        # the ticker symbols to make sure the right exchange name is returned.

        # PS: Before looping the result, must check for None, since it no iterable.
        # Then, it would raise an exception, which is not the desired behavior.

        result = MarkitOnDemand.lookup(ticker_symbol)

        if result is None:
            return None

        for item in result:
            if item['symbol'].lower() == ticker_symbol.lower():
                return item['exchange']

        # Should not arrive to this point. If it does, there's a error in the code above.
        raise TypeError("""Unsupported JSON object returned. Details:
                        \nLookup exchange for symbol: '{symbol}'.
                        \nJSON Object: {json_object}.
                        """.format(symbol=ticker_symbol, json_object=result))
