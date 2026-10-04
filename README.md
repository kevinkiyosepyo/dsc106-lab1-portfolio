# DSC 106 Lab 1 — Personal Portfolio

A plain HTML/CSS personal website created for
[DSC 106 Lab 1](https://dsc106.com/labs/lab01/).

- **Repository:** https://github.com/kevinkiyosepyo/dsc106-lab1-portfolio
- **Published site:** https://kevinkiyosepyo.github.io/dsc106-lab1-portfolio/

## Pages

| Path | Contents |
|---|---|
| `index.html` | Intro, local portrait, background, work history, and projects |
| `projects/index.html` | Links and descriptions for selected public projects |
| `resume/index.html` | Semantic HTML résumé using sections, articles, lists, links, and dates |
| `contact/index.html` | A labeled `mailto:` contact form |
| `style.css` | The one shared stylesheet used by every page |

Every page has relative navigation to all four pages and a GitHub profile link that
opens in a new tab. The design adapts to narrow viewports without horizontal scrolling.

## Run locally

```sh
python3 -m http.server 8777 --bind 127.0.0.1
```

Open http://127.0.0.1:8777/.

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 tests/browser_check.py
```

The browser checks exercise all pages at 320/390/768/1280px, navigation, keyboard
skip-link behavior, image loading, and native form validation. They intercept form
submission, so no email is sent during testing.

## Privacy note

This is an HTML adaptation of Kevin's résumé. It intentionally does **not** publish a
phone number, street address, date of birth, raw résumé PDF, credentials, or local
operational files. The contact page uses the deliberately simple `mailto:` form
contract required by the lab.
