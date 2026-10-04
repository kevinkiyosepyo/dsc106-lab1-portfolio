"""DSC 106 Lab 1 rubric tests for kevinpyo.com. Run: python3 -m unittest discover -s tests -v"""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "projects/index.html", "contact/index.html", "resume/index.html"]
GITHUB = "https://github.com/kevinkiyosepyo"


class Document(HTMLParser):
    """Minimal tag/attribute/text index for one page."""

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.tags = []
        self.texts = {}
        self._open = []
        self.text = path.read_text() if path.exists() else ""
        self.feed(self.text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        self._open.append(tag)

    def handle_endtag(self, tag):
        if tag in self._open:
            self._open.pop()

    def handle_data(self, data):
        if self._open:
            self.texts.setdefault(self._open[-1], []).append(data.strip())

    def elements(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]

    def text_of(self, tag):
        return [t for t in self.texts.get(tag, []) if t]


class LabRubricTests(unittest.TestCase):
    def test_every_page_is_a_well_formed_document_sharing_one_stylesheet(self):
        for page in PAGES:
            with self.subTest(page=page):
                path = ROOT / page
                self.assertTrue(path.is_file(), f"{page} is missing")
                doc = Document(path)
                self.assertEqual(len(doc.elements("h1")), 1, "exactly one <h1> per page")
                self.assertTrue(doc.text_of("title"), "page needs a <title>")
                self.assertTrue(any(m.get("charset") for m in doc.elements("meta")))
                self.assertTrue(any(m.get("name") == "viewport" for m in doc.elements("meta")))
                sheets = [l for l in doc.elements("link") if l.get("rel") == "stylesheet"]
                local = [l for l in sheets if not l["href"].startswith(("http", "//"))]
                self.assertEqual(len(local), 1, "exactly one local stylesheet link")
                self.assertEqual((path.parent / local[0]["href"]).resolve(), ROOT / "style.css")

    def test_stylesheet_uses_the_lab_body_font_shorthand(self):
        css = (ROOT / "style.css").read_text()
        self.assertIn("font: 100%/1.5 system-ui;", css)

    def test_homepage_titles_and_introduces_kevin_with_a_local_photo(self):
        doc = Document(ROOT / "index.html")
        self.assertIn("Kevin Kiyose Pyo: Personal site and portfolio", doc.text_of("title"))
        self.assertIn("kevin kiyose pyo", " ".join(doc.text_of("h1")).lower())
        self.assertTrue(doc.text_of("p"), "homepage needs a description paragraph")
        images = doc.elements("img")
        self.assertTrue(images, "homepage needs a local <img>")
        for image in images:
            self.assertTrue(image.get("alt", "").strip(), "every image needs alt text")
            self.assertFalse(image["src"].startswith(("http", "/")), "image must be a relative local file")
            self.assertTrue((ROOT / image["src"]).is_file(), f"missing file: {image['src']}")

    def test_navigation_reaches_every_page_relatively_plus_github_in_a_new_tab(self):
        for page in PAGES:
            with self.subTest(page=page):
                path = ROOT / page
                doc = Document(path)
                self.assertTrue(doc.elements("nav"), "page needs a <nav>")
                links = doc.elements("a")
                for destination in PAGES:
                    self.assertTrue(
                        any(
                            not a.get("href", "x").startswith(("http", "mailto:", "#", "/"))
                            and (path.parent / a["href"].split("#")[0]).resolve() == ROOT / destination
                            for a in links
                        ),
                        f"{page} has no relative link to {destination}",
                    )
                self.assertTrue(any(a.get("aria-current") == "page" for a in links), "current page not marked")
                github = [a for a in links if a.get("href") == GITHUB]
                self.assertTrue(github, "navigation needs a GitHub profile link")
                self.assertEqual(github[0].get("target"), "_blank")
                self.assertIn("noopener", github[0].get("rel", ""))

    def test_contact_page_implements_the_required_mailto_form(self):
        doc = Document(ROOT / "contact/index.html")
        forms = doc.elements("form")
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0].get("action"), "mailto:kevinkpyo@gmail.com")
        self.assertEqual(forms[0].get("method", "").upper(), "POST")
        self.assertEqual(forms[0].get("enctype"), "text/plain")
        fields = {f.get("name"): f for f in doc.elements("input") + doc.elements("textarea")}
        self.assertEqual(set(fields), {"email", "subject", "body"})
        self.assertEqual(fields["email"].get("type"), "email")
        self.assertEqual(len(doc.elements("label")), 3, "each field is wrapped in its own <label>")
        self.assertEqual(fields["email"].get("value"), "student@example.com")
        self.assertTrue(fields["subject"].get("value"), "subject has a development default")
        self.assertIn(">hello kevin,</textarea>", doc.text, "message has a development default")
        self.assertTrue(doc.elements("button"))
        self.assertFalse(doc.elements("table"), "do not lay the form out with a table")

    def test_resume_page_is_semantic_and_matches_kevins_real_history(self):
        doc = Document(ROOT / "resume/index.html")
        for tag in ["section", "article", "h2", "h3", "p", "ul", "li", "a", "time"]:
            self.assertTrue(doc.elements(tag), f"résumé is missing <{tag}>")
        self.assertTrue(all(s.get("aria-labelledby") for s in doc.elements("section")))
        times = doc.elements("time")
        self.assertTrue(all(t.get("datetime") for t in times), "every <time> needs a datetime")
        self.assertIn({"datetime": "2028-05"}, times, "expected graduation date")
        # The site's design language is lowercase, and names carry HTML entities,
        # so compare on decoded + case-folded text rather than exact casing.
        prose = unescape(doc.text).casefold()
        for fact in [
            "university of california, san diego",
            "data science",
            "qualcomm institute",
            "halıcıoğlu data science institute",
            "adobe",
            "handshake",
        ]:
            self.assertIn(fact, prose, f"résumé should mention {fact}")

    def test_projects_page_links_out_to_the_real_repositories(self):
        doc = Document(ROOT / "projects/index.html")
        self.assertTrue(doc.elements("article"), "each project is an <article>")
        hrefs = {a.get("href") for a in doc.elements("a")}
        for repo in ["Lightning-Data-Pipeline-API", "oncall-agent", "trends-for-forum"]:
            self.assertTrue(any(h and repo in h for h in hrefs), f"missing link to {repo}")

    def test_no_page_advertises_the_wrong_domain(self):
        for page in PAGES:
            with self.subTest(page=page):
                self.assertNotIn("kevin-kiyose-pyo.com", (ROOT / page).read_text())


if __name__ == "__main__":
    unittest.main()
