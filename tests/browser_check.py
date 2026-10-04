"""Browser acceptance checks; requires Playwright and installed Chrome."""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8777/")
    parser.add_argument("--output", default=str(ROOT / "artifacts"))
    args = parser.parse_args()
    base = args.url.rstrip("/") + "/"
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    routes = ["", "projects/", "resume/", "contact/"]
    report = {"base_url": base, "viewports": [], "errors": [], "form_delivery": "not attempted; submission intercepted to avoid opening an external mail application"}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        page.on("pageerror", lambda error: report["errors"].append(str(error)))
        page.on("console", lambda message: report["errors"].append(message.text) if message.type == "error" and "3847" not in message.text and "Failed to load resource" not in message.text else None)
        page.on("response", lambda response: report["errors"].append(f"HTTP {response.status}: {response.url}") if response.status >= 400 and "127.0.0.1:3847" not in response.url else None)
        for width in [320, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 900})
            for route in routes:
                response = page.goto(urljoin(base, route), wait_until="networkidle")
                assert response and response.ok, (route, response.status if response else None)
                assert page.locator("h1").count() == 1
                assert page.locator("nav.site-nav a[href]").count() >= 5
                assert page.locator("nav.site-nav a[aria-current='page']").count() == 1
                measurement = page.evaluate("""() => ({
                    viewport: innerWidth,
                    content: document.documentElement.scrollWidth,
                    brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src)
                })""")
                assert measurement["content"] <= width, (route, width, measurement)
                assert not measurement["brokenImages"], measurement
                report["viewports"].append({"route": route or "/", "width": width, "horizontal_overflow": False})
                if width in [390, 1280]:
                    page.screenshot(path=str(output / f"{route.strip('/') or 'home'}-{width}.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 900})
        for route in routes:
            page.goto(urljoin(base, route), wait_until="networkidle")
            links = page.locator("a[href]").evaluate_all("els => els.map(e => ({href:e.getAttribute('href'), absolute:e.href}))")
            for link in links:
                href = link["href"]
                if href.startswith(("https:", "mailto:")):
                    continue
                assert not href.startswith("/"), href
                local_url = urlparse(link["absolute"])
                result = context.request.get(link["absolute"].split("#")[0])
                assert result.ok, (route, href, result.status)
                if local_url.fragment:
                    checker = context.new_page()
                    checker.goto(link["absolute"], wait_until="domcontentloaded")
                    assert checker.locator(f'[id="{local_url.fragment}"]').count() == 1, link
                    checker.close()
        page.goto(base, wait_until="networkidle")
        for label, expected in [("projects", "projects/index.html"), ("resume", "resume/index.html"), ("contact", "contact/index.html"), ("home", "index.html")]:
            page.locator("nav.site-nav").get_by_role("link", name=label, exact=True).click()
            page.wait_for_url(urljoin(base, expected))
        report["navigation_clicks"] = "passed"
        page.goto(urljoin(base, "contact/"), wait_until="networkidle")
        page.evaluate("""() => {
            window.submissions = [];
            document.querySelector('form').addEventListener('submit', event => {
                event.preventDefault();
                window.submissions.push(Object.fromEntries(new FormData(event.target)));
            });
        }""")
        # The lab asks for development defaults. Clear them first so required
        # and email-type validation are still tested as the visitor would see it.
        page.get_by_label("your email").fill("")
        page.get_by_label("subject").fill("")
        page.get_by_label("message", exact=True).fill("")
        page.get_by_role("button", name="open email draft").click()
        assert page.evaluate("window.submissions.length") == 0
        page.get_by_label("your email").fill("invalid-email")
        page.get_by_label("subject").fill("Portfolio test — subject & symbols")
        page.get_by_label("message", exact=True).fill("Hello Kevin,\nTesting a multi-line message.")
        page.get_by_role("button", name="open email draft").click()
        assert page.evaluate("window.submissions.length") == 0
        page.get_by_label("your email").fill("reader@example.com")
        page.get_by_role("button", name="open email draft").click()
        submissions = page.evaluate("window.submissions")
        assert submissions == [{"email": "reader@example.com", "subject": "Portfolio test — subject & symbols", "body": "Hello Kevin,\nTesting a multi-line message."}], submissions
        assert page.locator("input, textarea").evaluate_all("els => els.every(e => e.labels.length > 0)")
        report["form_validation_and_submission"] = "passed"
        page.goto(base, wait_until="networkidle")
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.textContent") == "skip to content"
        page.keyboard.press("Enter")
        assert page.evaluate("location.hash") == "#main"
        report["keyboard_skip_link"] = "passed"
        assert not report["errors"], report["errors"]
        context.close()
        browser.close()
    report["passed"] = True
    (output / "browser-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
