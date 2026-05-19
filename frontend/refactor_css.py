import os

CSS_FILE = "src/styles.css"

with open(CSS_FILE, "r") as f:
    lines = f.readlines()

def write_css(filename, start_line, end_line):
    with open(f"src/styles/{filename}", "w") as f:
        f.writelines(lines[start_line - 1 : end_line])

os.makedirs("src/styles", exist_ok=True)

# lines 1-203: Base resets, variables, buttons, dashboard layouts
write_css("base.css", 1, 203)

# lines 205-322: Search lists and Alerts lists
write_css("lists.css", 205, 323)

# lines 324-383: Buttons, search-meta, forms
write_css("forms.css", 324, 384)

# lines 385-497: Test result cards, badges, grids, toggles
write_css("test-results.css", 385, 497)

# lines 498-677: Responsive design media queries
write_css("responsive.css", 498, 678)

# lines 679-823: Admin panel, dashboard nav, spinners, password toggle
write_css("admin-and-nav.css", 679, len(lines))

with open(CSS_FILE, "w") as f:
    f.write('''/* Global Stylesheet - Modularized */
@import "./styles/base.css";
@import "./styles/lists.css";
@import "./styles/forms.css";
@import "./styles/test-results.css";
@import "./styles/admin-and-nav.css";
@import "./styles/responsive.css";
''')

print("CSS Refactor complete.")
