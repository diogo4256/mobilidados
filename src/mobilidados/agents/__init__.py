"""Optional AI-assisted tools (``pip install 'mobilidados[agents]'``).

Design rule for everything in this package: the model proposes, deterministic code verifies. A model output
never becomes evidence by itself: quotes must be found verbatim in the cited source, values must be found in
the page's text layer or OCR (or are flagged for human review), and proposed data layers are re-queried.
"""
