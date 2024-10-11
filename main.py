import asyncio
import math
import httpx
from typing import TypedDict, List, Literal
from urllib.parse import urlencode
import json
from parsel import Selector
import time
import operator

session = httpx.AsyncClient(
    # for our HTTP headers we want to use a real browser's default headers to prevent being blocked
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    # Enable HTTP2 version of the protocol to prevent being blocked
    http2=True,
    # enable automatic follow of redirects
    follow_redirects=True
)

# this is scrape result we'll receive
class ProductPreviewResult(TypedDict):
    """type hint for search scrape results for product preview data"""

    url: str  # url to full product page
    title: str
    price: str
    shipping: str
    list_date: str
    subtitles: List[str]
    condition: str
    photo: str  # image url
    rating: str
    rating_count: str


def parse_search(response: httpx.Response) -> List[ProductPreviewResult]:
    """parse ebay's search page for listing preview details"""
    previews = []
    # each listing has it's own HTML box where all of the data is contained
    sel = Selector(response.text)
    listing_boxes = sel.css(".srp-results li.s-item")
    for box in listing_boxes:
        # quick helpers to extract first element and all elements
        css = lambda css: box.css(css).get("").strip()
        css_all = lambda css: box.css(css).getall()
        previews.append(
            {
                "url": css("a.s-item__link::attr(href)").split("?")[0],
                "title": css(".s-item__title>span::text"),
                "price": css(".s-item__price::text"),
                "shipping": css(".s-item__shipping::text"),
                "list_date": css(".s-item__listingDate span::text"),
                "subtitles": css_all(".s-item__subtitle::text"),
                "condition": css(".s-item__subtitle .SECONDARY_INFO::text"),
                "photo": css(".s-item__image img::attr(src)"),
                "rating": css(".s-item__reviews .clipped::text"),
                "rating_count": css(".s-item__reviews-count span::text"),
            }
        )
    return previews


SORTING_MAP = {
    "best_match": 12,
    "ending_soonest": 1,
    "newly_listed": 10,
}


async def scrape_search(query,max_pages=1000,category=0,items_per_page=240,sort: Literal["best_match", "ending_soonest", "newly_listed"] = "newly_listed",) -> List[ProductPreviewResult]:
    """Scrape Ebay's search for product preview data for given"""

    def make_request(page):
        print(page)
        return "https://www.ebay.com/sch/i.html?" + urlencode(
            {
                "_nkw": query,
                "_sacat": category,
                "_ipg": items_per_page,
                "_sop": SORTING_MAP[sort],
                "_pgn": page,
                "LH_BIN": 1
            }
        )
    first_page = await session.get(make_request(page=1))
    results = parse_search(first_page)
    if max_pages == 1:
        return results
    # find total amount of results for concurrent pagination
    total_results = Selector(first_page.text).css(".srp-controls__count-heading>span::text").get()
    total_results = int(total_results.replace(",", ""))
    total_pages = math.ceil(total_results / items_per_page)
    total_pages = max_pages
    other_pages = [session.get(make_request(page=i)) for i in range(2, total_pages + 1)]
    for response in asyncio.as_completed(other_pages):
        response = await response
        try:
            results.extend(parse_search(response))
        except Exception as e:
            print(f"failed to scrape search page {response.url}")
    return results

# Example run:
if __name__ == "__main__":
    import asyncio
    jszon = json.loads('[]')
    jzo = asyncio.run(scrape_search("Hard Drive"))
    for x in jzo:
      try:
        title = x['title'].lower()
        if 'tb' in title:
          size = ''
          if ((title[title.find("tb")-1] == ' ') or ((title[title.find("tb")-1].isnumeric() == False) and (title[title.find("tb")-1] != '.')) or (title.find("tb")-1 < 1)):
            ()
          else:
            size = str(title[title.find("tb")-1]) + size

          if ((title[title.find("tb")-2] == ' ') or ((title[title.find("tb")-2].isnumeric() == False) and (title[title.find("tb")-2] != '.')) or (title.find("tb")-2 < 1)):
            ()
          else:
            size = str(title[title.find("tb")-2]) + size

            if ((title[title.find("tb")-3] == ' ') or ((title[title.find("tb")-3].isnumeric() == False) and (title[title.find("tb")-3] != '.')) or (title.find("tb")-3 < 1)):
              ()
            else:
              size = str(title[title.find("tb")-3]) + size
              if ((title[title.find("tb")-4] == ' ') or ((title[title.find("tb")-4].isnumeric() == False) and (title[title.find("tb")-4] != '.')) or (title.find("tb")-4 < 1)):
                ()
              else:
                size = str(title[title.find("tb")-4]) + size
                if ((title[title.find("tb")-5] == ' ') or ((title[title.find("tb")-5].isnumeric() == False) and (title[title.find("tb")-5] != '.')) or (title.find("tb")-5 < 1)):
                  ()
                else:
                  size = str(title[title.find("tb")-3]) + size
          if str(size)[0] == '.':
            size = round(float(size))
          shipping = ''
          if (x['shipping'] == 'Free shipping') or (x['shipping'] == ''):
            shipping = '0'
          else:
            shipping = x['shipping'].replace('$', '').replace(' ','').replace('shipping', '').replace('+', '')
          pricepertb = (float(x['price'].replace('$', '').replace(',', 'x')) + float(shipping)) / float(size)
          pzo = {
            "title": x['title'],
            "price": x['price'],
            "size": size,
            "price per tb": pricepertb,
            "link": x['url'],
            "condition": x['condition'],

          }
          if x['condition'] != "Parts Only" and pricepertb > .2 and "sas" not in x['title'].lower():
            jszon.append(pzo)
      except Exception as e:
        print(e)
    jszon = sorted(jszon, key=lambda k: k['price per tb'], reverse=False)
    open('final.json', 'w').write(json.dumps(jszon, indent=4))