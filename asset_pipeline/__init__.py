"""Dreamer's asset pipeline.

Manifest-driven 2D asset generation for Godot games:
    generate -> post-process -> deterministic checks -> vision QA -> ledger.

Division of labor (see README §5): image generation is provider-pluggable;
Claude/vision is the *judge*, never the pixel generator; every property that
can be computed is asserted in code, and vision judges only the residue.
"""

__version__ = "0.1.0"
