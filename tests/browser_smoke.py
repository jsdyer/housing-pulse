"""Exercise the published tool at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.wait_for_selector("#content:visible")
                page.select_option("#period","2026-04")
                assert "2,400" in page.locator("#cards .big").first.inner_text()
                assert "3,030" in page.locator("#cards .big").last.inner_text()
                page.select_option("#metric","Average paid rent")
                page.select_option("#period","2026-04")
                assert "1,770" in page.locator("#cards .big").first.inner_text()
                page.select_option("#metric","Rental vacancy rate")
                page.select_option("#period","2025")
                assert "2.6%" in page.locator("#cards .big").first.inner_text()
                assert page.locator("#tablelink").get_attribute("href").endswith("3410013001")
                page.select_option("#metric","Housing completions")
                page.select_option("#kind","Total units")
                page.select_option("#left","Canada")
                page.select_option("#right","Canada")
                assert "Unavailable" not in page.locator("#cards .big").first.inner_text()
                page.select_option("#metric","Housing under construction")
                page.select_option("#period","1948-01")
                assert "29,510" in page.locator("#cards .big").first.inner_text()
                page.locator("#context-geo").select_option("British Columbia")
                page.locator("#context-common").click()
                assert "Unavailable" not in page.locator("#context-cards").inner_text()
                assert "British Columbia" in page.locator("#context-summary").inner_text()
                page.locator("#context-to").select_option("2025")
                assert "not published" in page.locator("#context-summary").inner_text()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, published values, filters and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
