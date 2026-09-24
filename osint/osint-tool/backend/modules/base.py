from abc import ABC, abstractmethod
from typing import Any, Dict


class OsintModule(ABC):
    """Base interface every recon module must implement.

    To add a new data source: subclass this, set `name` and `applies_to`,
    implement `run()`, then register an instance in main.py's MODULES dict.
    """

    name: str = "base"
    applies_to: tuple = ()  # e.g. ("domain",) or ("username",)

    @abstractmethod
    async def run(self, target: str) -> Dict[str, Any]:
        """Run the module against a target and return a JSON-serializable dict."""
        raise NotImplementedError
