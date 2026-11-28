"""Exercise the published tool at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_EXECUTABLE"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.wait_for_selector("#content:visible")
                series = json.loads((ROOT / "dist/data/edition.json").read_text())["series"]
                def check_card(first=True):
                    metric = page.locator("#metric").input_value()
                    kind = page.locator("#kind").input_value()
                    area = page.locator("#left" if first else "#right").input_value()
                    period = page.locator("#period").input_value()
                    cell = series[metric][kind][area].get(period)
                    value = cell[0] if isinstance(cell, list) else cell
                    expected = "Unavailable" if value is None else f"{value:,.2f}".rstrip("0").rstrip(".")
                    cards = page.locator("#cards .big")
                    assert expected in (cards.first if first else cards.last).inner_text()
                check_card()
                check_card(False)
                page.select_option("#metric","Average paid rent")
                check_card()
                page.select_option("#metric","Rental vacancy rate")
                check_card()
                assert page.locator("#tablelink").get_attribute("href").endswith("3410013001")
                page.select_option("#metric","Housing completions")
                page.select_option("#kind","Total units")
                page.select_option("#left","Canada")
                page.select_option("#right","Canada")
                assert "Unavailable" not in page.locator("#cards .big").first.inner_text()
                page.select_option("#metric","Housing under construction")
                page.select_option("#period","1948-01")
                check_card()
                page.locator("#context-geo").select_option("British Columbia")
                page.locator("#context-common").click()
                assert "Unavailable" not in page.locator("#context-cards").inner_text()
                assert "British Columbia" in page.locator("#context-summary").inner_text()
                coverage = json.loads((ROOT / "dist/data/context.json").read_text())["geographies"]["British Columbia"]
                latest_year = page.locator("#context-to option").last.get_attribute("value")
                page.locator("#context-to").select_option(latest_year)
                if coverage["completions"].get(latest_year, {}).get("value") is None:
                    assert "not published" in page.locator("#context-summary").inner_text()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                page.get_by_role("link", name="Find a city or province").click()
                page.get_by_role("link", name="Halifax", exact=True).click()
                assert page.get_by_role("heading", level=1).inner_text() == "What does it cost to rent in Halifax?"
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.get_by_role("link", name="Compare this market with another").click()
                page.wait_for_selector("#content:visible")
                assert page.locator("#left").input_value().startswith("Halifax,")
                assert page.locator("#right").input_value() == "All census metropolitan areas"
                check_card()
                page.go_back()
                page.get_by_role("link", name="Rent and earnings growth in Nova Scotia").click()
                page.get_by_role("link", name="Choose a different period in Housing Pulse").click()
                page.wait_for_function("document.querySelector('#context-geo').value === 'Nova Scotia'")
                reader = browser.new_context(java_script_enabled=False, viewport={"width": 320, "height": 640}).new_page()
                reader.goto(f"http://127.0.0.1:{server.server_port}/example-tool/records/")
                reader.get_by_role("link", name="Vancouver", exact=True).click()
                assert reader.get_by_role("table").count() == 2
                assert reader.evaluate("document.documentElement.scrollWidth <= innerWidth")
                reader.get_by_role("link", name="Rent and earnings growth in British Columbia").click()
                assert reader.get_by_role("table").count() == 1
                assert reader.evaluate("document.documentElement.scrollWidth <= innerWidth")
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, published values, filters and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
