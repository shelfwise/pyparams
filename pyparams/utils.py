import logging
import re
import subprocess
from argparse import ArgumentParser
from enum import Enum


def get_logger(
    name: str = "Logger",
    enable_stream_handler: bool = True,
    enable_file_handler: bool = False,
) -> logging.Logger:
    """
    Returns  Logger.
    Args:
        name: a name of the logger
        enable_stream_handler: add stream (console) handler to logger
        enable_file_handler: add file handler to logger

    Returns:
        logger: an instance of logging.Logger
    """
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s][%(filename)s/%(funcName)s]::%(message)s"
    )

    if enable_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)

    if enable_file_handler:
        file_handler = logging.FileHandler("log.txt")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


_DEFAULT_LOGGER = get_logger("pyparams")


def get_default_logger() -> logging.Logger:
    """
    Returns default Logger.
    """
    return _DEFAULT_LOGGER


_logger = get_default_logger()


class RunType(Enum):
    """Different run types implemented in manage.py script"""
    TRAIN = "train"
    EVAL = "eval"
    EXPORT = "export"
    FULL_EVAL = "full_eval"
    OPTIMIZE_NMS = "optimize_nms"
    OPTIMIZE_NET = "optimize_net"
    FINALIZE = "finalize"
    CLEAN = "clean"
    COMPILE = "compile"
    INIT = "init"
    GENERATE_REPORT = "generate_report"

    def __str__(self):
        return self.value


class RunMode(Enum):
    REGULAR = "regular"
    TRANSFER = "transfer"
    TRANSFER_AND_FREEZE = "transfer_and_freeze"
    FINETUNE = "finetune"

    def __str__(self):
        return self.value


class ArgumentParserWithDefaults(ArgumentParser):
    def add_argument(self, *args, help=None, default=None, **kwargs):
        if help is not None:
            kwargs["help"] = help
        if default is not None:
            kwargs["default"] = default
            if help is not None and default != "==SUPPRESS==":
                kwargs["help"] += f" ( default: {default} )"
        super().add_argument(*args, **kwargs)


def run_command(
    command_str: str, can_fail: bool = False, verbose: bool = True, **kwargs
) -> None:
    """Run bash command

    Args:
        command_str: a string command, can be multiline command
        can_fail: if True run command can fail when executing. This can be useful when
            removing not present file etc
        verbose: whether to print running command information or not
        **kwargs:

    """
    cmd_parts = [
        part for part in command_str.replace(" ", "\n").split("\n") if len(part) > 0
    ]

    if verbose:
        _logger.info(f"CMD: {' '.join(cmd_parts)}")

    if "check" not in kwargs:
        kwargs["check"] = True

    if can_fail:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
        kwargs["check"] = False

    subprocess.run(cmd_parts, **kwargs)


def add_subparser(subparsers, name: str, help_text: str, add_help: bool = True):
    """Creates new argparse subparser. This function was added to set `help`
    and `description` field equal, this will make that when calling `program --help`
    we will see nice subparser descrition as well as in case program subcommand --help.

    Args:
        subparsers: subparsers instance created with `parser.add_subparsers("subcommand")`
        name: a name of the subparser
        help_text: a help message
        add_help: whether to add -h/--help option or not

    Returns:
        a new subparser
    """
    return subparsers.add_parser(
        name,
        help=help_text,
        description=help_text,
        add_help=add_help,
    )


class REMatcher:
    """A helper class for matching groups in text, copied from SO """

    def __init__(self, matchstring: str):
        """
        Args:
            matchstring: a text to be matched with some pattern
        """
        self.matchstring = matchstring
        self.rematch = None

    def match(self, regexp: str) -> bool:
        """

        Args:
            regexp: a regex pattern

        Returns:
            whether regexp matches matchstring
        """
        self.rematch = re.match(regexp, self.matchstring)
        return bool(self.rematch)

    def group(self, i: int) -> str:
        """Access matched groups

        Args:
            i: index of the matched group

        Returns:
            matched group text
        """
        return self.rematch.group(i)


def convert_desc_field_to_comment(pyparam_yaml_config: str, indent: int) -> str:
    """Converts description field `desc` to comment in the YAML file, this makes
    YAML configs more readable for humans like we.

    Args:
        pyparam_yaml_config: a string with the content of the yaml config
        indent: yaml indentation i.e. a number of `space` characters
            before each paragraph

    Returns:
        new config in which keys `desc` are replaced with comments
            which start with `#` symbol
    """
    new_lines = []
    desc_lines = []
    for line in pyparam_yaml_config.split("\n"):
        # contains description ?
        if REMatcher(line).match(r"^[ ]*desc:(.*)"):
            desc_lines.append(line)
            continue

        # regular line
        if len(desc_lines) == 0:
            new_lines.append(line)
        else:
            desc_start_column = desc_lines[0].index("desc:")
            # long descriptions will have broken lines at
            # desc_start_column + indent - 1
            if line[desc_start_column + indent - 1] == " ":
                desc_lines.append(line)
            else:

                for row, desc_line in enumerate(desc_lines):
                    desc_line = desc_line.replace("desc:", "")
                    idx = desc_start_column
                    if row == 0:
                        desc_line = " " * idx + "#" + desc_line[idx:]
                    else:
                        desc_line = " " * idx + "#" + desc_line[idx + indent - 1 :]

                    new_lines.append(desc_line)

                new_lines.append(line)
                desc_lines = []

    return "\n".join(new_lines)


def convert_comment_to_desc_field(pyparam_yaml_config: str) -> str:
    """A reverse operation to convert_desc_field_to_comment. It reads the
    content of the yaml string and tries to replace comments with desc
    field. This function assumes that every comments is followed by dtype key.

    Args:
        pyparam_yaml_config: a string with the content of the yaml config

    Returns:
        new string yaml config with comments replaced with `desc` key
    """

    def has_pattern(_line: str, regex: str):
        return REMatcher(_line).match(regex)

    all_lines = pyparam_yaml_config.split("\n")
    new_lines = []
    num_lines = len(all_lines)
    for ln, line in enumerate(all_lines):
        # contains description ?
        if has_pattern(line, r"^[ ]*# (.*)"):
            is_first_line = has_pattern(all_lines[ln - 1], r"^[ ]*(\w+):")
            if is_first_line:
                k = 0
                search_test = False
                for k in range(num_lines - ln):
                    if has_pattern(all_lines[ln + 1 + k], r"^[ ]*dtype:"):
                        search_test = True
                        break

                if search_test:
                    desc_start_column = all_lines[ln + 1 + k].index("dtype:")
                    commented_lines = [
                        cl[desc_start_column + 1 :] for cl in all_lines[ln : ln + 1 + k]
                    ]
                    comment_line = "".join(commented_lines)
                    desc_line = " " * desc_start_column + "desc:" + comment_line
                    new_lines.append(desc_line)
                continue
        else:
            new_lines.append(line)

    return "\n".join(new_lines)
