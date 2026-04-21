from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URLS = [
    "http://itexps.net/",
    "http://itexps.net/about",
    "http://itexps.net/services",
    "http://itexps.net/contact",
]

def clean(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    all_text = ""
    for url in URLS:
        print(f"Scraping {url}...")
        try:
            # Using domcontentloaded + a manual wait is more reliable for Wix
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)  # Wait for JS to render the text
            all_text += f"\n=== {url} ===\n" + clean(page.content()) + "\n"
        except Exception as e:
            print(f"  Failed: {e}")
    browser.close()

with open("../data/site.txt", "w", encoding="utf-8") as f:
    f.write(all_text)

print("Done → data/site.txt")
