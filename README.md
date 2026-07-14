# A-Mart Static Grocery Offers Template

This is a plain static site for GitHub Pages. It has no build step and no backend.

## Update Daily Offers

Update `data/offers.json` and add product images under `assets/products/`.

Each product belongs to a category by `categoryId`. The optional `freeItem` object shows another product image and name when the offer includes a free item.

The site automatically adds an `All Offers` category on the landing page, so the updater only needs to write the real product categories.

```json
{
  "categoryId": "fruits",
  "name": "Apples 1 kg",
  "price": "Rs 120",
  "image": "assets/products/apples.png",
  "offer": "10% off today",
  "freeItem": {
    "name": "Lemon 250 g",
    "image": "assets/products/lemons.png"
  }
}
```

The future C++ updater can write `data/offers.json`, copy the latest local images into `assets/products/`, then commit and push.

## Run Locally

Use a local web server so the browser can load `data/offers.json`.

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000/`.

## Local Offer Editor

The local editor is a private tool for updating `data/offers.json` from a browser. It is not needed on GitHub Pages and should be run only on your computer.

On Windows, run:

```powershell
.\scripts\setup-admin.ps1
.\scripts\start-admin.ps1
```

Then open `http://127.0.0.1:9000/admin/`.

The editor uses only Python's standard library. If Python is missing and `winget` is available, the setup script will install Python first. The start script also checks for Python before launching. The editor can add categories, add/edit/remove products, choose local images, and save the updated JSON. Removed products do not delete image files from `assets/products/`.

## GitHub Pages

1. Push this folder to a GitHub repository.
2. In GitHub, open repository settings.
3. Go to Pages.
4. Set the source to deploy from the `main` branch and root folder.
5. Push future JSON/image updates to publish the latest offers.
