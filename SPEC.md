# Wisp Background Integration

## Requirement

Use the Darwin `public/wisp/` Three.js shader background as a static asset in the Streamlit UI. Do not port React/Vite components into the Streamlit app.

## Acceptance Criteria

- `darwin-main/public/wisp/` from `/Users/pratzz/Downloads/darwin-main.zip` is available at `static/wisp/`.
- `streamlit run ui/app.py` can find the same static assets through `ui/static`.
- `.streamlit/config.toml` enables Streamlit static file serving with `[server] enableStaticServing = true`.
- `ui/home.py` embeds `/app/static/wisp/index.html` as a fixed iframe at the start of `_HOME_TEMPLATE`'s `<body>`.
- The iframe sits behind the landing-page content, does not capture pointer events, and fills the viewport.
- Existing particle, dither, and mini-board background layers do not cover the Wisp iframe.
- Non-home Streamlit views such as build, analysis, and play also render the same Wisp background behind the app content.
- Streamlit's main app container stays above the Wisp iframe while page backgrounds remain transparent enough for the effect to be visible.
