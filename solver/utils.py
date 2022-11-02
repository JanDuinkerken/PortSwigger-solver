import logging
import math
import re
from collections import namedtuple
from http import HTTPStatus
from typing import Callable, Tuple, Any, Iterable, Optional, List

import requests
import valid8
from lxml import html
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, Task
from rich.table import Table

console = Console()
validate = valid8.validate

logging.basicConfig(
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, markup=True, rich_tracebacks=True)],
)
log = logging.getLogger("rich")

Credential = namedtuple("Credential", "username password")


def pattern(regex: str) -> Callable[[str], bool]:
    r = re.compile(regex)

    def res(value):
        return bool(r.fullmatch(value))

    res.__name__ = f'pattern({regex})'
    return res


def xpath(response, expression):
    html_document = html.fromstring(response.content)
    return html_document.xpath(expression)


def login(server, username, password):
    session = requests.Session()
    response = session.get(f"{server}/login")
    validate("Status Code", response.status_code, equals=HTTPStatus.OK)
    csrf_token = xpath(response, "//input[@name = 'csrf']/@value")[0]
    log.info(f"CSRF Token = {csrf_token}")
    response = session.post(f"{server}/login", data={
        "csrf": csrf_token,
        "username": username,
        "password": password,
    })
    validate("Status Code", response.status_code, equals=HTTPStatus.OK)
    return session


def submit_solution(server, answer):
    response = requests.post(f"{server}/submitSolution", data={
        "answer": answer,
    })
    validate("Status Code", response.status_code, equals=HTTPStatus.OK)
    return response.json()["correct"]


def verify_challenge_solved(server):
    response = requests.get(server)
    h4_elements = xpath(response, "//h4")
    solved = h4_elements[0].text == 'Congratulations, you solved the lab!'
    validate("Challenge solved", solved, equals=True)
    console.print("All done!")


BinarySearchCallback = Callable[[Tuple, Any, Any, Any], None]
GreaterThan = Callable[[Any], bool]


def binary_search_callback(
        header: Callable[[], Any] = None,
        footer: Callable[[], Any] = None,
        progress: Optional[Progress] = None,
        task: Optional[Task] = None,
        search_space_rows: List[Any] = None,
        search_space_row_index: int = 0,
        log_callback: Callable[[Table], None] = None,
        live: Optional[Live] = None,
) -> BinarySearchCallback:
    validate("", search_space_row_index, min_value=0, max_value=len(
        search_space_rows) - 1 if search_space_rows else 0)

    def callback(values, low, mid, high):
        grid = Table.grid()

        if header is not None:
            grid.add_row(header())

        worst_case = math.log2(high - low + 1)
        total_worst_case = math.ceil(math.log2(len(values)))
        if progress is not None:
            progress.update(task.id if task is not None else progress.task_ids[0],
                            completed=total_worst_case - worst_case,
                            total=total_worst_case,
                            visible=low < high or not progress.live.transient)
            grid.add_row(progress)
        elif task is not None:
            task.completed = total_worst_case - worst_case
            task.total = total_worst_case

        panel = Panel(
            ' '.join(
                f"[bold red]{elem}[/bold red]" if index == mid else
                f"[bold cyan]{elem}[/bold cyan]" if low <= index <= high else
                f"{elem}" for index, elem in enumerate(values)
            ),
            title=f"[yellow]Search space of {'of ' + task.description if task else ''}[/yellow]",
            subtitle=f"[red]tested value in red[/red] and [cyan]candidates in cyan[/cyan] - "
                     f"still [cyan]{high - low + 1}[/cyan] to go",
        )
        if search_space_rows:
            search_space_rows[search_space_row_index] = panel if low < high else None
            for row in search_space_rows:
                if row is not None:
                    grid.add_row(row)
        elif low < high:
            grid.add_row(panel)

        if footer is not None:
            grid.add_row(footer())

        if log_callback:
            log_callback(grid)

        if live is not None:
            live.update(grid)

    return callback


def binary_search_final_grid(
        header: Callable[[], Any] = None,
        footer: Callable[[], Any] = None,
        progress: Optional[Progress] = None,
) -> Table:
    grid = Table.grid()

    if header is not None:
        grid.add_row(header())

    if progress is not None:
        grid.add_row(progress)

    if footer is not None:
        grid.add_row(footer())

    return grid


def binary_search(sorted_iterable: Iterable, greater_than: GreaterThan,
                  callback: BinarySearchCallback = lambda values, low, mid, high: None):
    values = tuple(sorted_iterable)

    low = 0
    high = len(values) - 1

    while low < high:
        log.info(f"Binary search - number of candidates: {high - low + 1}")
        mid = (high + low) // 2
        if callback:
            callback(values, low, mid, high)
        if greater_than(values[mid]):
            low = mid + 1
        else:
            high = mid

    callback(values, low, low, low)
    return values[low]


def fetch_balance(server, session):
    response = session.get(f"{server}/my-account?id=wiener")
    current_balance = int(xpath(response, "//header[@class = 'navigation-header']/p/strong")[0].text.
                          split('$')[1].split('.')[0])
    log.info(f"Current balance is ${current_balance}")
    return current_balance


def fetch_csrf_token(server, session, endpoint):
    response = session.get(f"{server}{endpoint}")
    html_document = html.fromstring(response.content)
    csrf_token = html_document.xpath("//input[@name = 'csrf']/@value")[0]
    log.info(f"CSRF Token = {csrf_token}")
    return csrf_token


def add_item(server, session, product_id, quantity, redirect_to="PRODUCT"):
    response = session.post(f"{server}/cart", data={
        "productId": product_id,
        "redir": redirect_to,
        "quantity": quantity,
    })
    log.info(f"Status code = {response.status_code}")
    return response


def add_gift_card(server, session, quantity=1):
    add_item(server, session, product_id=2, quantity=quantity)


def add_dream_item(server, session, quantity=1):
    add_item(server, session, product_id=1, quantity=quantity)


def checkout(server, session, csrf_token):
    response = session.post(f"{server}/cart/checkout", data={
        "csrf": csrf_token,
    })
    return response
