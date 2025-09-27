import json
import os

import requests
from bs4 import BeautifulSoup


def get_mohu_data():
    url = "https://mohubudapest.hu/hulladeknaptar"

    district = os.environ.get("MOHU_DISTRICT")
    public_place = os.environ.get("MOHU_PUBLIC_PLACE")
    house_number = os.environ.get("MOHU_HOUSE_NUMBER")

    missing = [name for name, val in (
        ("MOHU_DISTRICT", district),
        ("MOHU_PUBLIC_PLACE", public_place),
        ("MOHU_HOUSE_NUMBER", house_number),
    ) if not val]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    # Step 1: Browser-like GET to initialize session
    page_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.6",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    }

    def make_headers(handler, partial):
        return {
            "Accept": "*/*",
            "Accept-Language": "en-GB,en;q=0.6",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "x-october-request-handler": handler,
            "x-october-request-partials": partial,
            "Origin": "https://mohubudapest.hu",
            "Referer": "https://mohubudapest.hu/hulladeknaptar",
            "User-Agent": page_headers["User-Agent"],
        }

    with requests.Session() as s:
        s.get(url, headers=page_headers)

        district_payload = {"district": district}
        district_headers = make_headers("onSelectDistricts", "ajax/publicPlaces")
        s.post(url, headers=district_headers, data=district_payload)

        public_place_payload = {"publicPlace": public_place}
        public_place_headers = make_headers("onSavePublicPlace", "ajax/houseNumbers")
        s.post(url, headers=public_place_headers, data=public_place_payload)

        search_payload = {"houseNumber": house_number}
        search_headers = make_headers("onSearch", "ajax/calSearchResults")
        resp = s.post(url, headers=search_headers, data=search_payload)

        data = resp.json()
        html = data["ajax/calSearchResults"]

        soup = BeautifulSoup(html, "html.parser")
        rows = []
        for tr in soup.select("tbody tr"):
            tds = tr.find_all("td")
            if len(tds) == 3:
                rows.append({
                    "day": tds[0].get_text(strip=True),
                    "date": tds[1].get_text(strip=True),
                    "services": [div.get_text(strip=True) for div in tds[2].find_all("div")]
                })

        print(json.dumps(rows, ensure_ascii=False, indent=2))

    return rows
