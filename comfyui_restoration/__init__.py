"""Local-first ComfyUI restoration workbench.

The package deliberately keeps media orchestration independent from ComfyUI.  ComfyUI is
an optional host; importing this package does not import torch or ComfyUI internals.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

WEB_DIRECTORY = "./web"
