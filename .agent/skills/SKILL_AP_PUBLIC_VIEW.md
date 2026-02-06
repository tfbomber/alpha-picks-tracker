---
name: AP Public View Mobile UI Spec (Updated)
description: Specification for the Alpha Picks Public View Mobile Interface
---

# Alpha Picks Public View - Mobile UI Specification

## 1. Core Principles
- **Mode**: Read-Only, Vertical Scrolling.
- **Goal**: "Premium" feel, high information density, immediate clarity.
- **Constraints**: Native Streamlit components only (`st.container`, `st.expander`, `st.columns`). No custom HTML/CSS for logic.

## 2. Layout Structure

### A. Focus Navigator (Top)
*   **Component**: `st.selectbox`
*   **Helper Text**: `需要着重关注的 APs`
*   **Format**: `Masked_Ticker | Picked <date> | Verdict` (e.g., `N*** | Picked 11/15/2023 | Imminent catalyst`)
*   **Purpose**: Single entry point effectively filters the view. No vertical stacking.
*   **Privacy**: Ticker MUST be masked (First letter + `***`).

### B. Now Viewing Anchor
*   **Component**: `st.container` (Bordered)
*   **Content**:
*   **Header**: `Ticker | Verdict`
*   **Purpose**: Context anchor since the dropdown collapses after selection.

### C. Deep Dive (Execution Dashboard)
*   **Section 1: Setup Card** (Always Visible)
    *   **Title**: `Setup · [Trigger Type]`
    *   **Metric**: `Price` (Single big number). *Removed Key Level/Delta to reduce clutter.*
    *   **Details**: 200-char summary + Expander for full text.
*   **Section 2: Action Plan** (Always Visible)
    *   **Title**: `AI Judgement · Action Plan`
    *   **Content**: 250-char summary + Expander.
*   **Section 3: Logic Pillars** (Tabs)
    *   **Tabs**: `Technical`, `Volume`, `News`, `Divergence`.
    *   **Content**: Full text analysis.

### D. Portfolio List (Inventory)
*   **Component**: Vertical stack of specific `st.container`.
*   **Sort/Filter**: Filter Input + Sort Selectbox (A-Z, Hold).
*   **Card Layout (4 Rows)**:
    1.  **Row 1**: `**Ticker** · Picked Date` (Left) | `Quant Label` (Right, e.g. Strong Buy)
    2.  **Row 2**: `Price` (Gray)
    3.  **Row 3 (Mini-Tech)**: `RSI 60.12 · Vol 1.15x · :green[>E21] :red[<S200]`
        *   *Precision*: 2 decimal places.
        *   *Trend*: Smart Summary relative to Price (No raw EMA values).
    4.  **Row 4 (Mini-Stats)**: `Earn: YYYY-MM-DD · Hold: 45d`
*   **Details Expander**:
    *   **Grades**: Val, Gro, Mom, Pro, Rev (All 5 grades).
    *   **Technical**: Full RSI, Vol, ATR%.
    *   **Trend**: Raw EMA21, EMA55, SMA200 values.

## 3. Style Guidelines
- **Colors**: Use `:green[]` and `:red[]` for financial data. Avoid generic emoji circles unless for status icons.
- **Spacing**: Use `st.columns` to create grid-like alignments within containers.
- **Density**: Keep row spacing compact on mobile; avoid extra blank lines between Price and RSI.
- **Privacy**: **ALWAYS** mask tickers in public views.
