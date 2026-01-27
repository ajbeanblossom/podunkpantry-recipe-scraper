from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

try:
    from recipe_scrapers import scrape_me
except Exception:
    scrape_me = None


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

        # Default fallback recipe – will always work
        recipe = {
            "source_url": recipe_url,
            "title": "Recipe from unsupported or test site",
            "description": "Either this site is not auto-supported yet, or scraping failed. Please review and edit.",
            "ingredients": [],
            "instructions": [],
            "servings": None,
            "total_time_minutes": None,
        }

        # Try scraping only if recipe-scrapers is available
        if scrape_me is not None:
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
                # Keep the fallback recipe, just attach the error for debugging
                recipe["error"] = str(e)

        body = json.dumps(recipe)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
        return
