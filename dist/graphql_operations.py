#!/usr/bin/env python
"""
Base GraphQL query method for other GraphQL applications to build on.
"""

import json
import time
import urllib.error

MAX_GRAPHQL_RETRIES = 10
GRAPHQL_RETRY_DELAY = 1.0


class GraphQLError(Exception):
    def __init__(self, error_list, message):
        self.error_list = error_list
        self.message = message


def try_graphql_query(client, query, var_data=None, logger=None,
                      max_retries=MAX_GRAPHQL_RETRIES, retry_delay=GRAPHQL_RETRY_DELAY):
    """
    Execute `query` on the client with any supplied parameters, retrying in
    case of transient server errors.
    """
    results = None
    retries = 0
    variables = {}
    while results is None:
        res_str = ""
        if logger is not None:
            logger.debug("Executing query:\n%s", query)
        if var_data:
            if logger is not None:
                logger.debug("Data:\n%s", var_data)
            variables = var_data
        try:
            res_str = client.execute(query, variables)
        except urllib.error.HTTPError as exc:
            if exc.code not in (502, 503):
                raise
            else:
                if logger is not None:
                    logger.info("Retrying GraphQL operation..")
                retries += 1
                if retries > max_retries:
                    raise
                else:
                    time.sleep(retry_delay)
        if res_str:
            if logger is not None:
                logger.debug("Result string:\n%s", res_str)
            try:
                results = json.loads(res_str)
            except json.decoder.JSONDecodeError:
                if logger is not None:
                    logger.error("Received invalid JSON response '%s', retrying", res_str)
                retries += 1
                if retries > max_retries:
                    raise
                else:
                    time.sleep(retry_delay)
            if results and 'errors' in results:
                raise(GraphQLError(results['errors'], "GraphQL operation failed"))
    return results
