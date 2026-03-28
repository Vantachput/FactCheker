Utilities
=========

Helpers
-------

Pure utility functions for text processing, time handling, and
Telegram Markdown escaping. Includes ``doctest``-compatible examples
that can be verified by running:
``python -m doctest utils/helpers.py -v``

.. automodule:: utils.helpers
   :members:
   :undoc-members:
   :show-inheritance:

Logger
------

Asynchronous AI usage analytics. Records every API call to two formats:
a human-readable ``bot_usage.log`` and a machine-readable
``usage_analytics.jsonl`` (JSON Lines). Automatically calculates the
cost in USD based on current provider pricing (OpenAI, Together AI,
Perplexity).

.. automodule:: utils.logger
   :members:
   :undoc-members:
   :show-inheritance:

Keyboards
---------

Inline keyboard factory functions for the Telegram bot UI.

.. automodule:: utils.keyboards
   :members:
   :undoc-members:
   :show-inheritance:
