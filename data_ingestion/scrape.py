from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os

PAGES = {
    "home": "http://itexps.net/",
    "about_us": "http://itexps.net/about-us",
    "programs": "http://itexps.net/services",
    "contact": "http://itexps.net/contact-us",
    "technicalmanagementprograms": "https://www.itexps.net/technicalmanagementprograms",
    "educationgrantprogram": "https://www.itexps.net/educationgrantprogram"
}

OUTPUT_DIR = "../data"

def clean(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def scrape_pages():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for name, url in PAGES.items():
            print(f"Scraping {name} → {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                cleaned_text = clean(page.content())

                output_path = os.path.join(OUTPUT_DIR, f"{name}.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {"title": name.replace("_", " ").title(), "content": cleaned_text},
                        f,
                        indent=2,
                        ensure_ascii=False
                    )

                print(f"  ✔ Saved {output_path}")

            except Exception as e:
                print(f"  ✖ Failed to scrape {url}: {e}")

        browser.close()

    print("\nDone! All pages saved in /data/")

if __name__ == "__main__":
    scrape_pages()
