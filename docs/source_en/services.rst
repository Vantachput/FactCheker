AI & Search Services
====================

AI Service
----------

Core AI engine. Abstracts interaction with three LLM providers:
OpenAI (GPT-4o, GPT-5), Together AI (Llama 3.1), and Perplexity (Sonar series).

Implements the **RAG (Retrieval-Augmented Generation)** pipeline:
user text → search query generation → Google search → source filtering → AI verdict.

.. automodule:: services.ai_service
   :members:
   :undoc-members:
   :show-inheritance:

Search Service
--------------

Google search engine wrapper using Serper.dev API.
Implements a **White List** source-filtering system with three trust tiers:

- **A+**: Official Ukrainian government domains (`*.gov.ua`)
- **A**: Global wire agencies (Reuters, BBC, AP News, Ukrinform)
- **B**: Quality independent media (Suspilne, Pravda Ukraine, Guardian)

.. automodule:: services.search_service
   :members:
   :undoc-members:
   :show-inheritance:
