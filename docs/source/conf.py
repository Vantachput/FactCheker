import os
import sys

os.environ['OPENAI_API_KEY'] = 'dummy'
os.environ['TOGETHER_API_KEY'] = 'dummy'
os.environ['SERPER_API_KEY'] = 'dummy'
os.environ['PERPLEXITY_API_KEY'] = 'dummy'
os.environ['BOT_TOKEN'] = '123456789:AAG_dummy_token_for_sphinx_build_test'

sys.path.insert(0, os.path.abspath('../..'))

project = 'FactChecker'
copyright = '2026, Author'
author = 'Author'
version = '1.0'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
