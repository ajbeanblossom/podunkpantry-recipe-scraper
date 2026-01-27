from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

from recipe_scrapers import scrape_me  # new import


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query string to get ?url=...
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        recipe_url = query.get("url", [""])[0]

        # Basic guard: if no URL, return an error
        if not recipe_url:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            body = json.dumps({"error": "Missing 'url' query parameter."})
            self.wfile.write(body.encode("utf-8"))
            return

        # Use recipe-scrapers to fetch and parse the recipe
        scraper = scrape_me(recipe_url)

        recipe = {
            "source_url": recipe_url,
            "title": scraper.title(),
            "description": scraper.description() or "",
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions_list(),
            "servings": scraper.yields(),
            "total_time_minutes": scraper.total_time(),
        }

        body = json.dumps(recipe)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
        return
