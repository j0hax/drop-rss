#!/bin/env python3

import http.server
import socketserver

from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from threading import Thread, Lock
import time

""" Cached feed string """
_feed_lock = Lock()
_feed_string = bytes()


def getFeed():
    fg = FeedGenerator()
    fg.title("Drop")
    fg.link(href="http://drop.com", rel="alternate")
    fg.description("Passions lead here")
    fg.language("en")
    URLs = [
        "https://drop.com/all-communities/drops/newest",
        "https://drop.com/all-communities/drops/refurbished",
    ]
    for URL in URLs:
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        items = soup.find_all(
            "a",
            class_=lambda value: value and value.startswith("Grid__gridItemInner__"),
            href=True,
        )
        for item in items:
            # Get Link
            rel_link = item["href"]
            drop_link = rel_link.split("/")[-1]
            # Get the data
            # We removed the parameter &returnMeta=true as it seems to always be empty
            data = requests.get(
                f"https://drop.com/api/drops;dropUrl={drop_link};isPreview=false;noCache=false;withPrices=true?lang=en-US"
            ).json()
            
            # Add everything to our feed
            try:
                fe = fg.add_entry()
                fe.id(str(data["id"]))
                if 'currentPrice' in data:
                    fe.title(f"[${data['currentPrice']}] {data['name']}")
                else:
                    fe.title(f"{data['name']}")
                fe.link(href=f"https://drop.com/buy/{data['url']}")
                fe.description(data["defaultDropBlurb"])
                fe.published(data["startAt"])
            except:
                print("Error generating entry.")
    return fg.rss_str()


def _update_feed(sleep=600):
    """ Updates the feed every x minutes """
    global _feed_string
    while True:
        with _feed_lock:
            _feed_string = getFeed()
            print("[Updated feed]")
        time.sleep(sleep)


class RSSHandler(http.server.SimpleHTTPRequestHandler):
    global _feed_string

    def do_GET(self):
        with _feed_lock:
            self.send_response(200)
            self.send_header("Content-type", "application/rss+xml")
            self.send_header("Content-length", len(_feed_string))
            self.end_headers()
            self.wfile.write(_feed_string)


if __name__ == "__main__":

    PORT = 8008
    with socketserver.TCPServer(("", PORT), RSSHandler) as httpd:
        updater = Thread(target=_update_feed, name="Feed-Updater", daemon=True)
        updater.start()
        print("serving at port", PORT)
        httpd.serve_forever()
