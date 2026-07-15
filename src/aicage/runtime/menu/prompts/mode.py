_PROMPT_MODE: dict[str, bool] = {"non_interactive_defaults": False}


def set_non_interactive_defaults(value: bool) -> None:
    _PROMPT_MODE["non_interactive_defaults"] = value


def non_interactive_defaults_enabled() -> bool:
    return _PROMPT_MODE["non_interactive_defaults"]
