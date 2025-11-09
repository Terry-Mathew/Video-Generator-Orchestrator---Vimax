from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, Type, TypeVar

import yaml

PipelineT = TypeVar("PipelineT", bound="BasePipeline")


class BasePipeline:
    """Shared helpers and configuration loader for pipeline implementations."""

    def __init__(self, working_dir: str | Path, **components: Any) -> None:
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

        for name, component in components.items():
            setattr(self, name, component)

    @staticmethod
    def load_config(path: str | Path) -> Dict[str, Any]:
        """Load a YAML configuration file into a dictionary."""
        with open(path, "r", encoding="utf-8") as source:
            return yaml.safe_load(source) or {}

    @staticmethod
    def _import_from_string(path: str) -> Any:
        """Import and return an attribute based on ``package.module:Class`` notation."""
        module_path, attr = path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, attr)

    @classmethod
    def _build_component(cls, block: Dict[str, Any]) -> Any:
        """Instantiate a component described by a config block."""
        class_path = block.get("class_path")
        if class_path:
            factory = cls._import_from_string(class_path)
            init_args = block.get("init_args", {})
            return factory(**init_args)
        # If no class path is provided, return the block unchanged so callers can handle it.
        return block

    @classmethod
    def init_from_config(cls: Type[PipelineT], config_path: str | Path) -> PipelineT:
        """
        Create a pipeline instance from a YAML config.

        Sections with a ``class_path`` key are instantiated automatically, while other
        sections are attached as-is for the concrete pipeline to handle.
        """
        raw_config = cls.load_config(config_path)

        working_dir = raw_config.pop("working_dir", ".working_dir")
        components: Dict[str, Any] = {}

        for name, block in raw_config.items():
            if isinstance(block, dict) and "class_path" in block:
                components[name] = cls._build_component(block)
            else:
                components[name] = block

        return cls(working_dir=working_dir, **components)

