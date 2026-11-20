module.exports = {
  "darkMode": "class",
  "theme": {
    "extend": {
      "colors": {
        "background": "#04060F",
        "surface": "#0B1020",
        "surface-dim": "#04060F",
        "surface-container-lowest": "#0B1020",
        "surface-container-low": "#0B1020",
        "surface-container": "#0B1020",
        "surface-container-high": "#181b26",
        "primary": "#4BB8E8",
        "primary-container": "#4BB8E8",
        "primary-fixed-dim": "#74d1ff",
        "on-primary": "#04060F",
        "on-primary-fixed": "#04060F",
        "on-primary-fixed-variant": "#04060F",
        "on-surface": "#EEF2F8",
        "on-background": "#EEF2F8",
        "on-surface-variant": "#A0B0C8",
        "secondary": "#A0B0C8",
        "tertiary": "#A0B0C8",
        "outline": "#738196",
        "error": "#ffb4ab"
      },
      "borderRadius": {
        "DEFAULT": "0.75rem",
        "full": "9999px"
      },
      "fontFamily": {
        "sans": [
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif"
        ]
      }
    }
  },
  "content": [
    "./features/ui/*.py"
  ]
};
