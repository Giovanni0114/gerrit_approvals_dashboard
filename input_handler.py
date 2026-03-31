from dataclasses import dataclass
from typing import Callable, Iterable

from models import AppContext

Context = dict[str, str]

ENDLINES = ("\r", "\n")
BACKSPACES = ("\x7f", "\x08")

PROMPTS_FOR_LAST_KEY = {
    " ": "Changes",
    "a": "Add change",
    "w": "Toggle waiting",
    "d": "Toggle disabled",
    "x": "Toggle deletion",
    "o": "Open change in web UI",
    "s": "Set Automerge +1",
}

# --------------------------------------------------------------------------------


def validator_int(input: str):
    return input.isnumeric()


# --------------------------------------------------------------------------------


def refresh(app_ctx: AppContext, ctx: Context) -> None:
    app_ctx.refresh_all()


def quit_app(app_ctx: AppContext, ctx: Context) -> None:
    app_ctx.quit()


# --------------------------------------------------------------------------------


def add_change(app_ctx: AppContext, ctx: Context) -> None:
    hash = ctx["hash"]
    host = ctx["host"]

    if len(hash) == 0:
        app_ctx.status_msg = f"[red]Invalid hash: \"{hash}\"[/red]"
        return

    app_ctx.add_change(hash, host)


def toggle_waiting(app_ctx: AppContext, ctx: Context) -> None:
    idx = ctx["idx"]

    if not validator_int(idx):
        app_ctx.status_msg = f"[red]Invalid idx: {idx} [/red]"
        return

    app_ctx.toggle_waiting(int(idx))


def handle_deletion(app_ctx: AppContext, ctx: Context) -> None:
    idx = ctx["idx"]

    if not validator_int(idx):
        app_ctx.status_msg = f"[red]Invalid idx: {idx} [/red]"
        return

    app_ctx.toggle_deleted(int(idx))


def toggle_disable(app_ctx: AppContext, ctx: Context) -> None:
    idx = ctx["idx"]

    if not validator_int(idx):
        app_ctx.status_msg = f"[red]Invalid idx: {idx} [/red]"
        return

    app_ctx.toggle_disabled(int(idx))


def open_change(app_ctx: AppContext, ctx: Context) -> None:
    idx = ctx["idx"]

    if not validator_int(idx):
        app_ctx.status_msg = f"[red]Invalid idx: {idx} [/red]"
        return

    app_ctx.open_change_webui(int(idx))


def set_automerge(app_ctx: AppContext, ctx: Context) -> None:
    idx = ctx["idx"]

    if not validator_int(idx):
        app_ctx.status_msg = f"[red]Invalid idx: {idx} [/red]"
        return

    app_ctx.set_automerge(int(idx))


# --------------------------------------------------------------------------------


@dataclass
class Action:
    action: Callable[[AppContext, Context], None]
    required_inputs: Iterable[str]


REFRESH_ACTION = Action(refresh, [])
QUIT_ACTION = Action(quit_app, [])

LEADER_ACTIONS = {
    "a": Action(add_change, ["hash", "host"]),
    "w": Action(toggle_waiting, ["idx"]),
    "d": Action(toggle_disable, ["idx"]),
    "x": Action(handle_deletion, ["idx"]),
    "o": Action(open_change, ["idx"]),
    "s": Action(set_automerge, ["idx"]),
}


def key_allowed_in_sequence(key: str, sequence: Iterable[str]) -> bool:
    if key == "<enter>":
        return True

    match sequence:
        case []:
            return key in (" ", "r", "q")
        case [" "]:
            return key in LEADER_ACTIONS

    return False


def match_action(key: str):
    match key:
        case "r":
            return REFRESH_ACTION

        case "q":
            return QUIT_ACTION

        case _:
            return LEADER_ACTIONS.get(key, None)


class InputHandler:
    def __init__(self, app_ctx: AppContext):
        self.app_context = app_ctx

        self.sequence: Iterable[str] = []
        self.input: str | None = None
        self.input_context_name: str | None = None
        self.context: dict[str, str] = {}

    def prompt(self, num_changes: int) -> str:
        if len(self.sequence) == 0:
            return ""

        if self.input is not None:
            hint = PROMPTS_FOR_LAST_KEY.get(self.sequence[-1])
            hint += f": {self.input_context_name}: {self.input}_ [ESC=cancel]"
            # TODO: hints aboud special characters
            # hint += "  [a=all submitted  x=purge deleted  r=restore all]"
            return hint

        return PROMPTS_FOR_LAST_KEY.get(self.sequence[-1])

    def handle_key(self, key: str) -> None:
        if key == "<esc>":
            self.reset()
            return

        self.handle_input(key)

        if self.input is not None:
            return

        if not key_allowed_in_sequence(key, self.sequence):
            self.app_context.status_msg = f"key not allowed in sequence : {key} {self.sequence}"
            return

        if key != "<enter>":
            self.sequence.append(key)

        action = match_action(self.sequence[-1])

        if action is None:
            return

        for required_input in action.required_inputs:
            if required_input not in self.context:
                self.input = ""
                self.input_context_name = required_input
                return

        action.action(self.app_context, self.context)

        self.reset()

    def reset(self) -> None:
        self.input = None
        self.input_context_name = None
        self.sequence = []
        self.context = {}

    def handle_input(self, key: str) -> None:
        if self.input is None:
            return

        if key == "<enter>":
            self.context[self.input_context_name] = self.input
            self.input = None
            self.input_context_name = None
            return

        if key == "<bs>":
            self.input = self.input[:-1]
            return

        self.input += key
