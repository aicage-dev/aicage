_PROMPT_MODE: dict[str, bool] = {"assume_yes": False}


def set_assume_yes(value: bool) -> None:
    _PROMPT_MODE["assume_yes"] = value


def assume_yes_enabled() -> bool:
    return _PROMPT_MODE["assume_yes"]
