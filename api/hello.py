from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

from recipe_scrapers import scrape_me


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        recipe_url = query.get("url", [""])[0]

        if not recipe_url:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            body = json.dumps({"error": "Missing 'url' query parameter."})
            self.wfile.write(body.encode("utf-8"))
            return

        try:
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

        except Exception as e:
            error_text = str(e)

            if "isn't currently supported by recipe-scrapers" in error_text:
                # Fallback for unsupported sites (like podunkliving.com with WP Recipe Maker)
                recipe = {
                    "source_url": recipe_url,
                    "title": "Recipe from unsupported site",
                    "description": "This site is not auto-supported yet. Please copy/paste or edit.",
                    "ingredients": [],
                    "instructions": [],
                    "servings": None,
                    "total_time_minutes": None,
                }
            else:
                # Other errors: still send a structured error back
                recipe = {
                    "source_url": recipe_url,
                    "title": "",
                    "description": "",
                    "ingredients": [],
                    "instructions": [],
                    "servings": None,
                    "total_time_minutes": None,
                    "error": error_text,
                }

        body = json.d
