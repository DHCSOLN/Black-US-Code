"""Index the published SOLN code documents and numbered executive orders."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

from lxml import html

BASE = "https://stateoflocnation.com/"
SOURCES = {
    "code": "usblack-code-house-gov",
    "orders": "solngpbc-executive-orders",
}
ORDER = re.compile(r"\b(?:EO|Executive[ _]+Order)[ _]+(?:No\.?[ _]+)?(\d{4})\b", re.I)


def read_records(group, source, markup):
    page = html.fromstring(markup)
    records = []
    seen = set()
    for section in page.xpath("//section[not(ancestor::header or ancestor::footer)]"):
        heading = section.xpath("string((.//h2)[1])").strip()
        if group == "code" and heading.startswith("Bill Declaration"):
            blocks = section.xpath(".//h2 | .//h4 | .//p[not(ancestor::li)] | .//li")
            body = "\n\n".join(
                " ".join(block.text_content().split()) for block in blocks
                if block.text_content().strip()
            )
            records.append(dict(title=heading, source=source, text=body))
        for link in section.xpath(".//a[@href]"):
            if ".pdf" not in link.get("href").lower():
                continue
            url = urljoin(source, link.get("href"))
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname != "img1.wsimg.com":
                continue
            if not parsed.path.lower().endswith(".pdf") or url in seen:
                continue
            title = " ".join(link.text_content().split()).removesuffix("Download").strip()
            title = title.removesuffix("(pdf)").strip()
            order = ORDER.search(title.replace("_", " "))
            if group == "orders" and not order:
                continue
            if group == "code" and not heading.startswith(("LOC CODE", "State of Loc Nation Global, Treaty")):
                continue
            seen.add(url)
            records.append(dict(title=title or heading, source=source, pdf=url,
                                number=order.group(1) if order else None))
    if not records:
        raise ValueError(f"No matching documents found at {source}")
    return records


def main():
    index = {}
    for group, path in SOURCES.items():
        source = urljoin(BASE, path)
        with urlopen(source, timeout=45) as response:
            index[group] = read_records(group, source, response.read())
        print(f"{group}: {len(index[group])} records")
    Path(sys.argv[1]).write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
