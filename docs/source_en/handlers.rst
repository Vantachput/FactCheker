Message Handlers
================

Command Handlers
----------------

Handles the ``/start`` command and sends the main menu keyboard to the user.

.. automodule:: handlers.command_handlers
   :members:
   :undoc-members:
   :show-inheritance:

Callback Handlers
-----------------

Handles inline keyboard button presses. Updates ``user_states`` dict
with the chosen AI method (base, together, openai_ft, sonar-*).

.. automodule:: handlers.callback_handlers
   :members:
   :undoc-members:
   :show-inheritance:

Message Handlers
----------------

The main business logic dispatcher. Parses incoming messages (plain text
or forwarded posts from channels/groups), enforces daily usage limits,
invokes the selected AI service, and returns the verdict.

Implements a **Fallback Algorithm**: if the smart search query yields
zero results, the system automatically retries with the raw user text.

.. automodule:: handlers.message_handlers
   :members:
   :undoc-members:
   :show-inheritance:
