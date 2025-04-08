#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime
import json
import random
import socket
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = sys.argv[1] if len(sys.argv) > 1 else "serie1"

feed_mapper = {
    "serie1": {
        "file": "serie1.json",
        "q": "?q=s%C3%A9rie:1",
        "title": "DRE Série 1",
    },
    "serie2": {
        "file": "serie2.json",
        "q": "?q=s%C3%A9rie:2",
        "title": "DRE Série 2",
    },
}

feed_vars = feed_mapper[FEED]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Firefox/64.0 Safari/537.36",
]

RSS_URL = "https://dre.tretas.org/dre/rss/" + feed_vars["q"]
OUTPUT_FILE = feed_vars["file"]


def parse_date(date_str):
    """Parses the date string, adds 11 days and returns it in the specified format.
    If the input is invalid, returns the original string.
    """
    try:
        dt = parsedate_to_datetime(date_str)
    except Exception:
        return date_str
    new_dt = dt + datetime.timedelta(days=11)
    return new_dt.strftime("%Y-%m-%dT%H-%M-%S.000")


def elem_to_dict(elem):
    """Recursively converts an XML element into a dictionary.
    This is used only to log the raw channel data as JSON.
    """
    d = {}
    for child in list(elem):
        tag = child.tag
        child_dict = elem_to_dict(child)
        if tag in d:
            if not isinstance(d[tag], list):
                d[tag] = [d[tag]]
            d[tag].append(child_dict)
        else:
            d[tag] = child_dict
    text = elem.text.strip() if elem.text else ""
    if d:
        if text:
            d["#text"] = text
    else:
        d = text
    return d


def fetch_and_save_rss():
    success = False
    tries = 0

    while not success:
        try:
            # Choose a random user-agent and send the HTTP request with a 10 second timeout
            user_agent = random.choice(user_agents)
            req = urllib.request.Request(RSS_URL, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise Exception("HTTP error! status: " + str(response.status))
                xml_data = response.read().decode("utf-8")

            # Parse the XML data using the built-in library
            root = ET.fromstring(xml_data)
            channel = root.find("channel")
            if channel is None:
                raise Exception("No channel found in RSS feed")

            # Extract channel description and items
            chan_description_el = channel.find("description")
            chan_description = (
                chan_description_el.text if chan_description_el is not None else ""
            )
            items = []
            for item in channel.findall("item"):
                guid_el = item.find("guid")
                title_el = item.find("title")
                description_el = item.find("description")
                pubDate_el = item.find("pubDate")
                # For dc:creator, check for any child element whose tag ends with 'creator'
                creator = ""
                for child in item:
                    if child.tag.split("}")[-1] == "creator":
                        creator = child.text if child.text is not None else ""
                        break
                items.append(
                    {
                        "id": guid_el.text if guid_el is not None else "",
                        "title": title_el.text if title_el is not None else "",
                        "description": description_el.text
                        if description_el is not None
                        else "",
                        "creator": creator,
                        "pubDate": parse_date(
                            pubDate_el.text if pubDate_el is not None else ""
                        ),
                    }
                )

            feed_json_data = {
                "title": feed_vars["title"],
                "description": chan_description,
                "items": items,
            }

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(feed_json_data, f, indent=2, ensure_ascii=False)

            channel_dict = elem_to_dict(channel)
            print(json.dumps(channel_dict, indent=2, ensure_ascii=False))
            success = True
        except Exception as error:
            tries += 1
            # Check if the error is due to a timeout
            if isinstance(error, urllib.error.URLError) and isinstance(
                error.reason, socket.timeout
            ):
                print(
                    "Error fetching or parsing RSS feed. Number of tries:",
                    tries,
                    "\n",
                    error,
                )
            else:
                success = True
                print(
                    "Error fetching or parsing RSS feed. Number of tries:",
                    tries,
                    "\n",
                    error,
                )


if __name__ == "__main__":
    fetch_and_save_rss()
