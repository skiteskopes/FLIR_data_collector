# Common area

Available Python modules:

* box_auth.py: Directs users to log into Box using their own credentials to allow an application to have read/write
  access to files stored on Box.

* terminal_progress_bar.py: Display a simple progress meter in a terminal window.  Also contains a ProgressFileWrapper
  class for showing file read or write progress.

* graphql_operations.py: Provides the base GraphQL method `try_graphql_query()` that other GraphQL classes build on.

* conservator_operations.py: Library of common GraphQL operations specific to the Conservator API.

* labelbox_operations.py: Library of common GraphQL operations specific to the Labelbox API.
