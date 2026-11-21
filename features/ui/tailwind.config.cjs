module.exports = {
  "darkMode": "class",
  "theme": {
    "fontSize": {
      "2xs": ["calc(0.8125rem * var(--ui-scale, 1))", { "lineHeight": "1.45" }],
      "xs": ["calc(0.875rem * var(--ui-scale, 1))", { "lineHeight": "1.5" }],
      "sm": ["calc(0.9375rem * var(--ui-scale, 1))", { "lineHeight": "1.55" }],
      "base": ["calc(1rem * var(--ui-scale, 1))", { "lineHeight": "1.6" }],
      "lg": ["calc(1.1875rem * var(--ui-scale, 1))", { "lineHeight": "1.45" }],
      "xl": ["calc(1.375rem * var(--ui-scale, 1))", { "lineHeight": "1.35" }],
      "2xl": ["calc(1.625rem * var(--ui-scale, 1))", { "lineHeight": "1.3" }],
      "3xl": ["calc(2rem * var(--ui-scale, 1))", { "lineHeight": "1.2" }],
      "4xl": ["calc(2.375rem * var(--ui-scale, 1))", { "lineHeight": "1.15" }]
    },
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
