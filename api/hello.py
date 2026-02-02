from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re

import requests


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1) Read ?url=... from the query string
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        recipe_url = query.get("url", [""])[0]

        if not recipe_url:
            self._send_json(
                400,
                {"error": "Missing 'url' query parameter."}
            )
            return

        try:
            # 2) Fetch the HTML of the page
            resp = requests.get(recipe_url, timeout=10)
            resp.raise_for_status()
            html = resp.text

            # 3) Find all <script type="application/ld+json"> blocks
            scripts = re.findall(
                r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )

            recipe_data = None

            for raw_script in scripts:
                try:
                    data = json.loads(raw_script.strip())
                except Exception:
                    continue

                def iter_candidates(obj):
                    # If it's a plain dict, yield it and its @graph children
                    if isinstance(obj, dict):
                        yield obj
                        graph = obj.get("@graph")
                        if isinstance(graph, list):
                            for node in graph:
                                if isinstance(node, dict):
                                    yield node
                    # If it's a list, yield each dict item
                    elif isinstance(obj, list):
                        for item in obj:
                            if isinstance(item, dict):
                                yield item

                for item in iter_candidates(data):
                    # Look for @type "Recipe" (could be list or string)
                    type_field = item.get("@type")
                    if isinstance(type_field, list):
                        types = [t.lower() for t in type_field if isinstance(t, str)]
                    elif isinstance(type_field, str):
                        types = [type_field.lower()]
                    else:
                        types = []

                    if "recipe" in types:
                        recipe_data = item
                        break

                if recipe_data is not None:
                    break

            if recipe_data is None:
                # No recipe JSON-LD found
                result = {
                    "source_url": recipe_url,
                    "title": "",
                    "description": "",
                    "ingredients": [],
                    "instructions": [],
                    "servings": None,
                    "total_time_minutes": None,
                    "image_url": None,
                    "error": "No schema.org Recipe JSON-LD found on this page.",
                }
                self._send_json(200, result)
                return

            # 4) Map schema.org fields into a simple structure
            title = recipe_data.get("name", "") or ""
            description = recipe_data.get("description", "") or ""

            # Ingredients
            ingredients = recipe_data.get("recipeIngredient", [])
            if not isinstance(ingredients, list):
                ingredients = [str(ingredients)]

            # Instructions can be various formats
            instructions_field = recipe_data.get("recipeInstructions", [])
            instructions = []

            if isinstance(instructions_field, list):
                for step in instructions_field:
                    if isinstance(step, dict) and "text" in step:
                        instructions.append(str(step["text"]))
                    else:
                        instructions.append(str(step))
            elif isinstance(instructions_field, str):
                instructions = [instructions_field]
            else:
                instructions = []

            # Servings
            servings = recipe_data.get("recipeYield")
            if isinstance(servings, list):
                servings = servings[0] if servings else None

            # Total time (ISO 8601 like "PT30M")
            total_time_iso = recipe_data.get("totalTime")
            total_minutes = None
            if isinstance(total_time_iso, str) and total_time_iso.startswith("PT"):
                # Very simple parser: look for number + "M"
                match = re.search(r"(\d+)\s*M", total_time_iso)
                if match:
                    total_minutes = int(match.group(1))

            # Image (can be string or list or dict)
            image_field = recipe_data.get("image")
            image_url = None

            if isinstance(image_field, str):
                image_url = image_field
            elif isinstance(image_field, list) and image_field:
                first = image_field[0]
                if isinstance(first, str):
                    image_url = first
                elif isinstance(first, dict):
                    image_url = first.get("url") or first.get("@id")
            elif isinstance(image_field, dict):
                image_url = image_field.get("url") or image_field.get("@id")

            result = {
                "source_url": recipe_url,      # 5. root URL
                "title": title,                # 1. title
                "description": description,
                "ingredients": ingredients,    # 2. ingredients
                "instructions": instructions,  # 3. instructions
                "servings": servings,
                "total_time_minutes": total_minutes,
                "image_url": image_url,        # 4. image URL
            }

            self._send_json(200, result)
            return

        except Exception as e:
            # Catch-all error so the function never crashes
            result = {
                "source_url": recipe_url,
                "title": "",
                "description": "",
                "ingredients": [],
                "instructions": [],
                "servings": None,
                "total_time_minutes": None,
                "image_url": None,
                "error": str(e),
            }
            self._send_json(500, result)
            return

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload)
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
