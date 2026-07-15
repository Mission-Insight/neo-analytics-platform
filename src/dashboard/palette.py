"""
Shared chart color palette for the dashboard's reference palette.
Categorical slots referenced by comments elsewhere in src/dashboard/
(e.g. "slot 1 (blue)") all resolve back to the values defined here.
"""

BLUE = {"light": "#2a78d6", "dark": "#3987e5"}
GREEN = {"light": "#1baf7a", "dark": "#199e70"}
AMBER = {"light": "#eda100", "dark": "#c98500"}
DARK_GREEN = {"light": "#008300", "dark": "#008300"}
RED = {"light": "#e34948", "dark": "#e66767"}
VIOLET = {"light": "#4a3aa7", "dark": "#9085e9"}

# Diverging pair (blue <-> red, neutral gray midpoint) for -1..+1 scales.
DIVERGING = {
    "light": {"low": BLUE["light"], "mid": "#f0efec", "high": RED["light"]},
    "dark": {"low": BLUE["dark"], "mid": "#383835", "high": RED["dark"]},
}
