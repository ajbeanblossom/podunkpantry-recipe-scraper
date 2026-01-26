from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query string to get ?url=...
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        recipe_url = query.get("url", [""])[0]

        # For now, return fake recipe data (we'll hook real scraping in later)
        recipe = {
            "source_url": recipe_url,
            "title": "Test Podunk Pantry Recipe",
            "description": "This is sample data from the Podunk Pantry scraper endpoint.",
            "ingredients": [
                "2 cups flour",
                "1 cup sugar",
                "2 eggs"
            ],
            "instructions": [
                "Preheat oven to 350 F.",
                "Mix all ingredients in a bowl.",
                "Bake for 25 minutes."
            ],
            "servings": 4,
            "total_time_minutes": 30
        }

        body = json.dumps(recipe)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
        return
