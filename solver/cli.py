import dataclasses
import logging
from enum import Enum
from tkinter import W
from typing import Optional

import typer
from urllib3.util import parse_url

from solver.labs import sql_1
from solver.utils import console, validate, pattern

from termcolor import colored

LAB_DOMAIN = "web-security-academy.net"


class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


@dataclasses.dataclass(frozen=True)
class AppOptions:
    server: str = dataclasses.field(default='00000000000000000000000000000000')
    log_level: LogLevel = dataclasses.field(default=LogLevel.WARNING)
    debug: bool = dataclasses.field(default=False)

    def with_debug(self) -> 'AppOptions':
        return AppOptions(
            server=self.server,
            log_level=self.log_level,
            debug=True,
        )


app_options = AppOptions()
app = typer.Typer()


def is_debug_on():
    return app_options.debug


def run_app():
    try:
        app()
    except Exception as e:
        if is_debug_on():
            raise e
        else:
            console.print(colored(f"Error: {e}", 'red', attrs=['bold']))


@app.callback()
def main(
        server: str = typer.Option(
            ...,
            prompt=True,
            envvar="SID",
            help=f"Vulnerable server ID (subdomain of {LAB_DOMAIN})."
        ),
        log_level: Optional[LogLevel] = typer.Option(
            None,
            show_default=False,
            help="Set log level. Default to WARNING (or DEBUG if --debug is used)."
        ),
        debug: bool = typer.Option(False, "--debug", help="Enable debug."),
):
    print(colored("\n\n Jan Duinkerken's PortSwigger Academy solver \n",
          'yellow', attrs=['bold']))
    print(colored("""\
            ////////////////    ///////////////
            ////////////////    ///////////////
            ///////////////     ///////////////
            /////////////     /////////////////
            ///////////     ///////////////////
            /////////           ///////////////
            ///////             ///////////////
            ////////////////    ///////////////
            ////////////////            *//////
            ////////////////          *////////
            ///////////////////*    ///////////
            /////////////////,    /////////////
            ////////////////    ///////////////
            ////////////////    /////////////// 
          """, 'yellow', attrs=['bold']))
    print("\n")
    global app_options

    if debug:
        app_options = app_options.with_debug()

    validate("server", server, length=32, custom=[pattern(
        r"[0-9a-f]*")], help_msg="Server ID must be 32 digits.")

    if log_level is None:
        log_level = LogLevel.DEBUG if debug else LogLevel.WARNING

    app_options = AppOptions(
        server=parse_url(f"https://{server}.{LAB_DOMAIN}"),
        log_level=log_level,
        debug=debug,
    )
    logging.getLogger().setLevel(app_options.log_level.value)


@app.command()
def sql_vulnerability_in_where_clause() -> None:

    print(colored("SQL injection vulnerability in WHERE clause allowing retrieval of hidden data\n",
          'blue', attrs=['bold']))

    sql_1.main(
        server=app_options.server
    )
