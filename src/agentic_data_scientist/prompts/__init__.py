"""Prompt templates and loading utilities."""

from pathlib import Path
from typing import Optional


def load_prompt(name: str, domain: Optional[str] = None) -> str:
    """
    Load prompt template by name.

    Parameters
    ----------
    name : str
        Prompt name (e.g., 'plan_generator', 'coding_review')
    domain : str, optional
        Optional domain namespace (e.g., 'bioinformatics')

    Returns
    -------
    str
        Prompt template string

    Raises
    ------
    FileNotFoundError
        If the prompt file doesn't exist
    """
    prompts_dir = Path(__file__).parent

    if domain:
        prompt_path = prompts_dir / "domain" / domain / f"{name}.md"
    else:
        prompt_path = prompts_dir / "base" / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")

    return prompt_path.read_text()


__all__ = ["load_prompt"]
