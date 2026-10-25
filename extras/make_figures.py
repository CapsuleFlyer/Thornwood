"""Screenshot the figures used in debrief.pdf out of extras/visual.html.

Needs Playwright (pip install playwright, then: playwright install chromium).
NOT part of the submission.  Run from the repo root:  python extras/make_figures.py
Writes extras/figures/*.png (light theme, 2x resolution).
"""
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")


def shot(page, selector, path, pad=8):
    """Screenshot an element with a little padding so outer rings are not clipped."""
    loc = page.locator(selector)
    loc.scroll_into_view_if_needed()
    box = loc.bounding_box()
    scroll = page.evaluate("window.scrollY")
    page.screenshot(path=path, full_page=True, clip={
        "x": box["x"] - pad, "y": box["y"] + scroll - pad,
        "width": box["width"] + 2 * pad, "height": box["height"] + 2 * pad})


def main():
    os.makedirs(FIG, exist_ok=True)
    page_url = "file://" + os.path.join(HERE, "visual.html").replace(os.sep, "/")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=2,
                                color_scheme="light")
        page.goto(page_url)
        page.wait_for_timeout(400)

        # Q1: hill climbing from (0,0), showing the whole path (the page opens on it)
        shot(page, "#gridSvg", os.path.join(FIG, "hill_climb.png"))

        # Q3: genetic algorithm, generation 50 against the true best
        shot(page, "#chart", os.path.join(FIG, "ga_chart.png"))

        # Q4: Stone Drop after X drops in column 0 and Vesper answers in column 2
        page.locator("#colpick button").nth(0).click()
        shot(page, "#board", os.path.join(FIG, "board_x0.png"))

        # Q5: node counts as bars
        shot(page, "#ki", os.path.join(FIG, "ki_bars.png"), pad=4)
        browser.close()
    print("wrote", ", ".join(sorted(os.listdir(FIG))))


if __name__ == "__main__":
    main()
