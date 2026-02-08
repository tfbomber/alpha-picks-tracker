---
name: AP Public View Mobile UI Spec (Updated)
description: Specification for the Alpha Picks Public View Mobile Interface
---

# Alpha Picks Public View - Mobile UI Specification

## 1. Core Principles
- **Mode**: Read-Only, Vertical Scrolling.
- **Goal**: "Premium" feel, high information density, immediate clarity.
- **Constraints**: Native Streamlit components only (`st.container`, `st.expander`, `st.columns`). No custom HTML/CSS for logic.
- **Mobile Detection**: Auto-detect via `navigator.userAgent` (no manual toggle). Session state key: `mobile_view`.

## 2. Layout Structure

### A. Focus Navigator (Top)
*   **Component**: `st.selectbox` (label collapsed)
*   **Header**: `st.subheader("Key APs to watch")`
*   **Sync Line**: `st.caption("Last Synced: {updated_at}")`
*   **Format**: `Masked_Ticker | Picked <date> | Verdict` (e.g., `N*** | Picked 01/15/2026 | Imminent catalyst`)
*   **Purpose**: Single entry point effectively filters the view. No vertical stacking.
*   **Privacy**: Ticker MUST be masked (First letter + `*` repeated).

### A2. Focus Scan Row (Optional)
*   **When used**: Public view displays a Focus List scan row.
*   **Format**: One-line, fixed 6 fields:
    `Ticker | Setup | Tech | Distance | Catalyst | Urgency/News`
*   **Distance**: Always `price vs SMA200 %` (primary risk gauge).
*   **Tech**: `below/above + key line + confirm days` (e.g., `below SMA200 (3d)`).

### B. Deep Dive (Execution Dashboard)
*   **A) One-line Verdict**
    *   **Format**: `RISK_OFF / No Entry - ER -3d + price -18.7% below SMA200, trend bearish.`
    *   **Price Source**: Must use `latest_price + price_type + price_timestamp` only.
*   **B) Evidence (<=5 lines)**
    1. Price / Timestamp / Session (Last/Close/Pre-Mkt)
    2. Key Levels: SMA200/EMA55/EMA21 + distance%
    3. Volume: RVOL20 + one-line explanation
    4. News: Top 1-2 headlines + time
    5. Divergence: e.g., `SA Buy vs price trend`
*   **C) Playbook (Quantized)**
    *   Ban: `until ER passed + 2 sessions`
    *   Watch Trigger (Primary): `close reclaim SMA200`
    *   Watch Trigger (Secondary): `2 closes above EMA21`
    *   Failure: `reject at EMA21 with RVOL<1`
    *   Next action: `watch only / add alert / remove from focus`

### C. Portfolio List (Inventory)
*   **Component**: Vertical stack of `st.container(border=True)`.
*   **Sort/Filter**: Filter Input + Sort Selectbox (Ticker A-Z, Hold Desc).
*   **Card Layout (4 Rows)**:
    1.  **Row 1**: `**Ticker** · Picked Date` (Left, `.mobile-picked`) | `Quant Label` (Right, `.mobile-quant`, e.g. Strong Buy)
    2.  **Row 2**: `Price` (`.mobile-price`)
    3.  **Row 3 (Mini-Tech)**: `RSI 60.12 · Vol 1.15x · :green[>E21] :red[<S200]` (`st.caption`)
        *   *Precision*: 2 decimal places.
        *   *Trend*: Smart Summary relative to Price (No raw EMA values).
    4.  **Row 4 (Mini-Stats)**: `Earn: YYYY-MM-DD · Hold: 45d` (`st.caption`)
*   **Details Expander** (`st.expander("Details")`):
    *   **Grades**: Val, Gro, Mom, Pro, Rev (All 5 grades in 5 columns).
    *   **Technical** (left column): Full RSI, Vol Ratio, ATR%.
    *   **Trend** (right column): Raw EMA21, EMA55, SMA200 values with `:green[]`/`:red[]` color-coded comparison to price.
    *   **Earnings**: Earnings date.
    *   **Hold Streak**: Hold duration in days.

## 3. Style Guidelines
- **Colors**: Use `:green[]` and `:red[]` for financial data. Avoid generic emoji circles unless for status icons.
- **Spacing**: Use `st.columns` to create grid-like alignments within containers.
- **Density**: Keep row spacing compact on mobile; avoid extra blank lines between Price and RSI.
- **Privacy**: **ALWAYS** mask tickers in public views.
  - **Mask rule**:
    - 1 letter: `A*`
    - 2 letters: `A*`
    - 3 letters: `A**`
    - 4+ letters: `A***Z` (first + last, middle all `*`)

## 4. Dark Mode CSS Architecture

### Mechanism: CSS `light-dark()` function
Streamlit sets `color-scheme: light` or `color-scheme: dark` as an inline style on `.stApp`. The CSS `light-dark(lightVal, darkVal)` function reads this inherited property and returns the correct value.

**Why NOT `@media (prefers-color-scheme)` or `[data-theme="dark"]`:**
- `@media (prefers-color-scheme: dark)` tracks OS preference, NOT Streamlit's theme toggle
- Streamlit does NOT set `data-theme`, `.streamlit-dark`, or `.dark` class — these selectors are dead code
- `light-dark()` is the only pure-CSS approach that correctly tracks Streamlit's actual theme state

### Color Palette (in `style/style.css`)

| Element | Light Mode | Dark Mode | CSS Class |
|---------|-----------|-----------|-----------|
| Price text | `#1e40af` (Blue 800) | `#93c5fd` (Blue 300) | `.mobile-price`, `.mobile-setup-price` |
| Quant signal | `#4338ca` (Indigo 700) | `#a5b4fc` (Indigo 300) | `.mobile-quant` |
| Picked date | `#6b7280` (Gray 500) | `#9ca3af` (Gray 400) | `.mobile-picked` |
| Headings | `#0f172a` (Slate 900) | `#f8fafc` (Slate 50) | `h1, h2, h3`, `.mobile-title` |
| Metrics | `#1e293b` / `#64748b` | `#f8fafc` / `#94a3b8` | `stMetricValue`, `stMetricLabel` |

### Specificity Boosters
Streamlit injects custom HTML via `unsafe_allow_html=True` into `div[data-testid="stMarkdownContainer"]`. Higher-specificity selectors ensure overrides work:
```css
div[data-testid="stMarkdownContainer"] .mobile-price { ... }
div[data-testid="stMarkdownContainer"] .mobile-setup-price { ... }
```

### Fallback
`@supports not (color: light-dark(black, white))` block at file end provides `@media (prefers-color-scheme: dark)` fallback for older browsers. Browser support for `light-dark()`: Chrome 123+, Firefox 120+, Safari 17.5+ (all since mid-2024).
