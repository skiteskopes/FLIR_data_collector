#!/usr/bin/python3
"""
Base class for Labelbox-specific GraphQL queries and mutations.
"""

import json
import logging
from graphql_operations import try_graphql_query


class LabelboxOperations(object):
    """
    Perform GraphQL queries and mutations using the Labelbox API.
    """
    def __init__(self, client, logger=None):
        self.client = client
        self.logger = logger
        if self.logger is None:
            self.logger = logging.getLogger("LabelboxOperations")

    def get_project_id(self, project_name):
        """
        Get the Labelbox ID for `project_name`.
        """
        var_data = {"name": project_name}
        res = try_graphql_query(self.client, """
        query projectImageCount($name: String!) {
          projects(where: { name: $name }) {
            id
          }
        }
        """, json.dumps(var_data), self.logger)

        proj_id = None
        if 'projects' in res['data'] and res['data']['projects']:
            proj_id = res['data']['projects'][0]['id']
        return proj_id

    def get_image_count(self, project_name):
        """
        Get the number of images associated with `project_name`.
        """
        var_data = {"name": project_name}
        res = try_graphql_query(self.client, """
        query projectImageCount($name: String!) {
          projects(where: { name: $name }) {
            dataRowCount
          }
        }
        """, json.dumps(var_data), self.logger)

        count = 0
        if 'projects' in res['data'] and res['data']['projects']:
            count = res['data']['projects'][0]['dataRowCount']
        return count

    def get_project_image_info(self, project_name, row_count=10, row_skip=0):
        """
        Get both Labelbox and Conservator IDs for every frame in
        `project_name`.
        """
        var_data = {"name": project_name, "first": row_count, "skip": row_skip}
        res = try_graphql_query(self.client, """
        query projectImageInfo($name: String!, $first: PageSize, $skip: Int) {
          projects(where: { name: $name }) {
            dataRows(first: $first, skip: $skip) {
              id
              deleted
              externalId
              rowData
            }
          }
        }
        """, json.dumps(var_data), self.logger)

        image_info = {}
        if 'projects' in res['data'] and res['data']['projects']:
            image_info = res['data']['projects'][0]['dataRows']
        return image_info
