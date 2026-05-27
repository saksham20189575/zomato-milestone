"""TasteTrail AI dark theme — global Streamlit CSS."""

from __future__ import annotations

import streamlit as st

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: radial-gradient(ellipse 120% 80% at 50% -20%, #1a1a24 0%, #0a0a0f 45%, #060608 100%);
    color: #e8e8ec;
}

#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* Nav */
.tt-nav {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 2.5rem;
}
.tt-nav-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #2a2a35 0%, #1a1a22 100%);
    border: 1px solid #333340;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
}
.tt-nav-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.02em;
}

/* Hero */
.tt-hero {
    text-align: center;
    margin-bottom: 2rem;
}
.tt-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: #9ca3af;
    margin-bottom: 1.25rem;
}
.tt-hero h1 {
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin: 0 0 0.75rem 0;
    color: #fff;
    line-height: 1.1;
}
.tt-hero h1 .muted {
    color: #6b7280;
    font-weight: 600;
}
.tt-hero p {
    color: #9ca3af;
    font-size: 1.05rem;
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.5;
}

/* Form card wrapper */
.tt-form-shell {
    background: rgba(22, 22, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 1.75rem 1.75rem 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 24px 48px rgba(0,0,0,0.35);
}

/* Field labels */
label[data-testid="stWidgetLabel"] p,
.stSlider label p {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #6b7280 !important;
}

/* Inputs */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div {
    background-color: #121218 !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 12px !important;
    color: #f3f4f6 !important;
}
.stSelectbox > div > div { min-height: 44px; }

/* Radio budget pills */
div[data-testid="stRadio"] > div {
    flex-direction: row !important;
    gap: 0.5rem;
    background: transparent !important;
}
div[data-testid="stRadio"] > div > label {
    background: #121218 !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 12px !important;
    padding: 0.55rem 1.25rem !important;
    color: #9ca3af !important;
    font-weight: 500 !important;
    flex: 1;
    justify-content: center;
}
div[data-testid="stRadio"] > div > label[data-checked="true"],
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: #e8e8ec !important;
    border-color: #e8e8ec !important;
    color: #111 !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #22d3ee !important;
    border-color: #22d3ee !important;
}
.stSlider [data-baseweb="slider"] div[data-testid="stThumbValue"] {
    display: none;
}

/* Number input */
.stNumberInput button {
    background: #1a1a22 !important;
    border-color: #2a2a35 !important;
    color: #fff !important;
}

/* Primary CTA */
.stFormSubmitButton > button {
    background: linear-gradient(180deg, #f0f0f2 0%, #d4d4d8 100%) !important;
    color: #111 !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.85rem 1.5rem !important;
    margin-top: 0.5rem;
    box-shadow: 0 4px 20px rgba(255,255,255,0.12);
}
.stFormSubmitButton > button:hover {
    background: #fff !important;
}

/* Rating value display */
.tt-rating-value {
    text-align: right;
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    margin-top: -2.2rem;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 2;
}

/* Results section */
.tt-results-header {
    font-size: 1.5rem;
    font-weight: 700;
    color: #fff;
    margin: 2rem 0 1.25rem;
    letter-spacing: -0.02em;
}
.tt-summary {
    background: rgba(34, 211, 238, 0.08);
    border: 1px solid rgba(34, 211, 238, 0.25);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    color: #a5f3fc;
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 1.5rem;
}
.tt-alert-fallback {
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid rgba(251, 191, 36, 0.3);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    color: #fcd34d;
    font-size: 0.875rem;
    margin-bottom: 1rem;
}
.tt-empty {
    text-align: center;
    padding: 3rem 1rem;
    color: #6b7280;
}
.tt-empty h3 { color: #9ca3af; margin-bottom: 0.5rem; }

/* Restaurant cards */
.tt-card {
    background: #14141c;
    border: 1px solid #252530;
    border-radius: 16px;
    padding: 1.1rem 1.15rem 1rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.tt-card:hover {
    border-color: #3a3a48;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.tt-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.35rem;
}
.tt-rank {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: #6b7280;
}
.tt-match {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #22d3ee;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.35);
    border-radius: 6px;
    padding: 0.2rem 0.45rem;
}
.tt-card-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.65rem;
}
.tt-card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #fff;
    margin: 0;
    letter-spacing: -0.02em;
}
.tt-heart {
    color: #4b5563;
    font-size: 1.1rem;
}
.tt-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem 1rem;
    font-size: 0.8rem;
    color: #9ca3af;
    margin-bottom: 0.5rem;
}
.tt-meta-row span { display: inline-flex; align-items: center; gap: 0.25rem; }
.tt-cost {
    color: #22d3ee !important;
    font-weight: 600;
}
.tt-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-bottom: 0.85rem;
}
.tt-tag {
    font-size: 0.68rem;
    color: #9ca3af;
    background: #1a1a22;
    border: 1px solid #2a2a35;
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
}
.tt-ai-box {
    background: #0e0e14;
    border: 1px solid #1f1f28;
    border-radius: 12px;
    padding: 0.75rem 0.85rem;
    margin-top: auto;
}
.tt-ai-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #6b7280;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}
.tt-ai-text {
    font-size: 0.78rem;
    color: #9ca3af;
    font-style: italic;
    line-height: 1.45;
    margin: 0;
}

/* Loading */
.tt-loading {
    text-align: center;
    padding: 3rem;
    color: #9ca3af;
}
.tt-loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #2a2a35;
    border-top-color: #22d3ee;
    border-radius: 50%;
    animation: tt-spin 0.8s linear infinite;
    margin: 0 auto 1rem;
}
@keyframes tt-spin { to { transform: rotate(360deg); } }

div[data-testid="stExpander"] {
    background: #14141c;
    border: 1px solid #252530;
    border-radius: 12px;
}
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_nav() -> None:
    st.markdown(
        """
        <div class="tt-nav">
            <div class="tt-nav-icon">🍴</div>
            <span class="tt-nav-title">TasteTrail AI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="tt-hero">
            <div class="tt-badge">✦ DISCOVER THE FUTURE OF DINING</div>
            <h1>TasteTrail <span class="muted">AI</span></h1>
            <p>Personalized restaurant discovery powered by AI and real-world dining preferences.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
