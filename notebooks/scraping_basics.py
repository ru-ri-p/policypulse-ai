# notebooks/scraping_basics.py — Week 2 Day 8
import requests
from bs4 import BeautifulSoup

# requests.get() sends an HTTP GET request — like your browser visiting a URL
response = requests.get("https://httpbin.org/get", timeout=30)

# Every response has a status code:
# 200 = success, 404 = not found, 403 = forbidden, 500 = server error
print("Status code:", response.status_code)

# response.text is the raw HTML (or JSON) of the page
print("Content (first 200 chars):", response.text[:200])

# Headers tell the server who is making the request
headers = {
    "User-Agent": "PolicyPulse Research Bot 1.0 (academic use)",
}
response = requests.get("https://httpbin.org/get", headers=headers, timeout=30)
print("With headers:", response.status_code)

# Fetch a real page
response = requests.get("https://quotes.toscrape.com", headers=headers, timeout=30)

# Parse the HTML — "lxml" is the parser (fast and forgiving of bad HTML)
soup = BeautifulSoup(response.text, "lxml")

title = soup.find("title")
print("Page title:", title.text if title else "N/A")

quotes = soup.find_all("span", class_="text")
for quote in quotes[:3]:
    print(quote.text)

author = soup.select_one(".author")
print("First author:", author.text if author else "Not found")
