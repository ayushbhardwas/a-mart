#!/usr/bin/env python3
import base64
import json
import mimetypes
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "offers.json"
BACKUP_FILE = ROOT / "data" / "offers.backup.json"
PRODUCTS_DIR = ROOT / "assets" / "products"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_BODY_BYTES = 15 * 1024 * 1024


def read_json():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        BACKUP_FILE.write_text(DATA_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_text(value):
    return value.strip() if isinstance(value, str) else ""


def normalize_offer_data(payload):
    categories = payload.get("categories")
    products = payload.get("products")
    if not isinstance(categories, list) or not isinstance(products, list):
        raise ValueError("Categories and products must be lists.")

    normalized_categories = []
    category_ids = set()
    for category in categories:
        if not isinstance(category, dict):
            continue
        category_id = clean_text(category.get("id"))
        name = clean_text(category.get("name"))
        if not category_id or not name:
            continue
        if category_id in category_ids:
            raise ValueError(f"Duplicate category id: {category_id}")
        category_ids.add(category_id)
        normalized_categories.append({"id": category_id, "name": name})

    normalized_products = []
    for product in products:
        if not isinstance(product, dict):
            continue
        category_id = clean_text(product.get("categoryId"))
        if category_id not in category_ids:
            raise ValueError(f"Product category does not exist: {category_id}")

        normalized = {
            "categoryId": category_id,
            "name": clean_text(product.get("name")),
            "price": clean_text(product.get("price")),
            "image": clean_text(product.get("image")),
            "offer": clean_text(product.get("offer")),
        }
        if not all(normalized.values()):
            raise ValueError("Every product needs category, name, price, image, and offer text.")

        free_item = product.get("freeItem")
        if isinstance(free_item, dict):
            free_name = clean_text(free_item.get("name"))
            free_image = clean_text(free_item.get("image"))
            if free_name or free_image:
                if not free_name or not free_image:
                    raise ValueError("Free items need both a name and an image.")
                normalized["freeItem"] = {"name": free_name, "image": free_image}

        normalized_products.append(normalized)

    return {
        "updatedAt": clean_text(payload.get("updatedAt")) or date.today().isoformat(),
        "categories": normalized_categories,
        "products": normalized_products,
    }


def safe_site_path(raw_path):
    request_path = unquote(urlparse(raw_path).path)
    if request_path == "/":
        request_path = "/index.html"
    if request_path == "/admin":
        request_path = "/admin/"
    if request_path == "/admin/":
        request_path = "/admin/index.html"

    relative = request_path.lstrip("/")
    resolved = (ROOT / relative).resolve()
    if ROOT not in resolved.parents and resolved != ROOT:
        raise ValueError("Path is outside the site.")
    return resolved


def safe_product_image_path(relative_path):
    relative = clean_text(relative_path).replace("\\", "/").lstrip("/")
    resolved = (ROOT / relative).resolve()
    if PRODUCTS_DIR not in resolved.parents:
        raise ValueError("Images must be saved under assets/products.")
    if resolved.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Image must use png, jpg, jpeg, webp, or gif.")
    return resolved


def save_uploaded_images(images):
    if not isinstance(images, list):
        raise ValueError("Images must be a list.")

    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    for image in images:
        if not isinstance(image, dict):
            continue
        path = safe_product_image_path(image.get("path"))
        data_url = clean_text(image.get("dataUrl"))
        match = re.match(r"^data:image/[a-zA-Z0-9.+-]+;base64,(.+)$", data_url)
        if not match:
            raise ValueError("Invalid image data.")
        path.write_bytes(base64.b64decode(match.group(1), validate=True))


class AdminHandler(BaseHTTPRequestHandler):
    server_version = "AMartAdmin/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/offers"):
            try:
                self.send_json(200, read_json())
            except Exception as error:
                self.send_json(500, {"error": str(error)})
            return

        try:
            path = safe_site_path(self.path)
            if not path.exists() or not path.is_file():
                self.send_error(404, "File not found")
                return
            body = path.read_bytes()
            content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except ValueError as error:
            self.send_error(403, str(error))

    def do_POST(self):
        if not self.path.startswith("/api/save"):
            self.send_error(404, "Unknown API endpoint")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_BODY_BYTES:
                raise ValueError("Save request is too large.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            data = normalize_offer_data(payload)
            save_uploaded_images(payload.get("images", []))
            write_json(data)
            self.send_json(200, {"ok": True, "data": data})
        except Exception as error:
            self.send_json(400, {"error": str(error)})


def main():
    host = "127.0.0.1"
    port = 9000
    server = ThreadingHTTPServer((host, port), AdminHandler)
    print(f"A-Mart local editor: http://{host}:{port}/admin/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
