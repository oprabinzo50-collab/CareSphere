#!/usr/bin/env python3
"""Apply the CareSphere UI upgrade to a local CareSphere checkout."""
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
app = root / "frontend/src/App.tsx"
main = root / "frontend/src/main.tsx"
index = root / "frontend/index.html"
css_src = Path(__file__).parent / "frontend/src/electronics-inspired.css"
css_dst = root / "frontend/src/electronics-inspired.css"

for p in (app, main, index):
    if not p.exists():
        raise SystemExit(f"Expected file not found: {p}")

# Add styling hooks without changing application behavior.
src = app.read_text(encoding="utf-8")
src = src.replace(
    '<div style={styles.loginPage}>',
    '<div style={styles.loginPage} className="care-login-page">',
)
src = src.replace(
    '<div style={styles.loginCard}>',
    '<div style={styles.loginCard} className="care-login-card">',
)
app.write_text(src, encoding="utf-8")

main_src = main.read_text(encoding="utf-8")
if "electronics-inspired.css" not in main_src:
    main_src = main_src.replace(
        "import './caresphere.css'\n",
        "import './caresphere.css'\nimport './electronics-inspired.css'\n",
    )
main.write_text(main_src, encoding="utf-8")

html = index.read_text(encoding="utf-8")
html = html.replace("<title>frontend</title>", "<meta name=\"theme-color\" content=\"#101b33\" />\n    <meta name=\"description\" content=\"CareSphere — secure healthcare intelligence and care coordination.\" />\n    <title>CareSphere | Clinical Intelligence</title>")
index.write_text(html, encoding="utf-8")
shutil.copy2(css_src, css_dst)
print("UI upgrade files applied. Next: cd frontend && npm run build && npm run lint")
