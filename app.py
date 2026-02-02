import streamlit as st
import pandas as pd
import json
import os
import re
import html
import html
from datetime import datetime
from streamlit_javascript import st_javascript


# --- Configuration ---
st.set_page_config(
    page_title="AP Market Overview",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Mobile Logic ---
def is_mobile_device():
    # Helper to get User Agent via JS
    ua = st_javascript("navigator.userAgent")
    if not ua:
        return False # Default to Desktop if undetected
    mobile_keywords = ['Android', 'webOS', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'Windows Phone']
    return any(keyword in ua for keyword in mobile_keywords)

def render_mobile_cards(df):
    """Renders the Portfolio DataFrame as a vertical list of HTML Cards"""
    if df is None or df.empty:
        st.info("No Active Picks")
        return

    # Iterate rows
    for index, row in df.iterrows():
        # Prepare Data
        ticker = row.get('ticker', 'N/A')
        # Check if ticker is masked logic or raw string
        # (Assuming 'ticker' col is already masked in main, but let's be safe)
        
        price = row.get('price', 0)
        day_pct = row.get('Day%', 0)
        signal = row.get('quant', 'Hold') # Using 'quant' emoji as signal or raw text
        
        # Color Logic for Day%
        pct_color = "#10b981" if day_pct >= 0 else "#ef4444"
        pct_str = f"{day_pct:+.2f}%"

        # Grades Visuals
        val = row.get('value_grade', '-')
        gro = row.get('growth_grade', '-')
        mom = row.get('momentum_grade', '-')
        
        # Card HTML
        card_html = f"""
        <div class="mobile-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>
                    <span style="font-size: 1.2rem; font-weight: 700; color: #1e293b;">{ticker}</span>
                    <div style="font-size: 0.85rem; color: #64748b;">${price:.2f}</div>
                </div>
                <div style="text-align: right;">
                     <div style="font-size: 1rem; font-weight: 600; color: {pct_color};">{pct_str}</div>
                     <div style="font-size: 0.8rem; color: #64748b;">{signal}</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid #f1f5f9; padding-top: 8px; font-size: 0.8rem;">
                <span>Val: <b>{val}</b></span>
                <span>Gro: <b>{gro}</b></span>
                <span>Mom: <b>{mom}</b></span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Expandable Details
        with st.expander("Details", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.caption("Technical")
                st.write(f"RSI: {row.get('rsi14', '-')}")
                st.write(f"Vol Ratio: {row.get('vol', '-')}")
            with c2:
                st.caption("Trend")
                st.write(f"EMA21: {row.get('ema21', '-')}")
                st.write(f"SMA200: {row.get('sma200', '-')}")
            st.caption(f"Earnings: {row.get('earnings', '-')}")
            st.caption(f"Streak: {row.get('hold_streak_days', '-')} Days")


# Path Resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "data", "snapshot.json")
STYLE_PATH = os.path.join(BASE_DIR, "style", "style.css")

if os.path.exists(STYLE_PATH):
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Removed st.cache_data to prevent stale snapshot loading
def load_data():
    if not os.path.exists(SNAPSHOT_PATH):
        return None
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def strip_evidence_refs(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    cleaned = re.sub(r"\s*\((?:[A-Z]\d+(?:,\s*)?)+\)", "", text)
    cleaned = re.sub(r"\b[FNVB]\d+\b", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = cleaned.replace(" ,", ",").replace(" .", ".")
    return cleaned

def mask_ticker(ticker: str) -> str:
    if ticker is None:
        return ""
    value = str(ticker).strip()
    if not value:
        return ""
    star_count = max(1, len(value) - 1)
    return f"{value[0]}{'*' * star_count}"

def main():
    data = load_data()
    if not data:

def main():
    data = load_data()
    if not data:
        st.error("System Offline: Snapshot missing.")
        return

    meta = data.get("meta", {})
    updated_at = meta.get("updated_at", "Unknown")

    # --- Header ---
    c_title, c_toggle = st.columns([0.8, 0.2])
    with c_title:
        st.title("Performance Overview")
        st.caption(f"Last Synced: {updated_at}")
    
    with c_toggle:
        # Auto-Detect Mobile (Only runs once ideally, but Streamlit reruns might re-trigger)
        # We use session_state to hold the "auto-detected" preference once.
        if "first_load" not in st.session_state:
            is_mobile = is_mobile_device()
            st.session_state.mobile_view = is_mobile
            st.session_state.first_load = True
        
        use_mobile = st.toggle("📱 View", value=st.session_state.get("mobile_view", False), key="mobile_view_toggle")
        # Update session state if toggled
        st.session_state.mobile_view = use_mobile

    st.divider()

    # --- 1. Focus List (Interactive) ---
    st.markdown("### Focus List (Top 8)")
    st.caption("Urgency-ranked signals with AI verdicts")
    
    focus_items = data.get("focus_view_model", [])
    
    if focus_items:
        # Initialize Selection
        ticker_list = [item.get('ticker') for item in focus_items]
        if 'focus_selected' not in st.session_state or st.session_state.focus_selected not in ticker_list:
            if ticker_list:
                st.session_state.focus_selected = ticker_list[0]
        
        # --- Responsive Focus List ---
        # If Mobile: Vertical Stack. If Desktop: 4 Columns.
        if st.session_state.mobile_view:
             # Vertical Stack for Mobile
            for i, item in enumerate(focus_items):
                # Render item logic (Extract for reuse or duplicate carefully)
                # ... (Duplication for safety and minor UI tweaks) ...
                
                verdict = item.get('verdict', 'WATCH')
                ticker = item.get('ticker')
                picked_date = item.get('picked_date')
                reason = item.get('reason', '')
                urgency_val = item.get('urgency')
                signal = item.get('signal') or '—'
                news = item.get('news') or '—'
                is_selected = (ticker == st.session_state.focus_selected)

                # Urgency Format
                if urgency_val is None:
                    urgency_str = "N/A"
                else:
                    try:
                        urgency_float = float(urgency_val)
                        if urgency_float == 0.0 and "Excluded" in str(reason):
                            urgency_str = "Excluded"
                        else:
                            urgency_str = f"{urgency_float:.1f}"
                    except (TypeError, ValueError):
                        urgency_str = str(urgency_val)

                # Container
                with st.container(border=True):
                     c_info, c_btn = st.columns([0.7, 0.3])
                     with c_info:
                        picked_display = str(picked_date).strip() if picked_date else "N/A"
                        ticker_value = str(ticker).strip() if ticker else ""
                        if ticker_value:
                            star_count = max(1, len(ticker_value) - 1)
                            display_core = f"{ticker_value[0]}{'*' * star_count}"
                        else:
                            display_core = "N/A"
                        
                        st.markdown(f"**{display_core}** | {verdict}")
                        st.caption(f"Urgency {urgency_str} | {signal}")
                     
                     with c_btn:
                        btn_type = "primary" if is_selected else "secondary"
                        # Use a unique key ensures state tracking
                        if st.button("Select", key=f"mob_btn_{ticker}_{i}", use_container_width=True, type=btn_type):
                            st.session_state.focus_selected = ticker
                            st.rerun()

        else:
            # Standard Desktop 4-Column Grid
            cols = st.columns(4)
            for i, item in enumerate(focus_items):
                with cols[i % 4]:
                    verdict = item.get('verdict', 'WATCH')
                    ticker = item.get('ticker')
                    picked_date = item.get('picked_date')
                    reason = item.get('reason', '')
                    urgency_val = item.get('urgency')
                    signal = item.get('signal') or '—'
                    news = item.get('news') or '—'
                    
                    is_selected = (ticker == st.session_state.focus_selected)
    
                    if urgency_val is None:
                        urgency_str = "N/A"
                    else:
                        try:
                            urgency_float = float(urgency_val)
                            if urgency_float == 0.0 and "Excluded" in str(reason):
                                urgency_str = "Excluded"
                            else:
                                urgency_str = f"{urgency_float:.1f}"
                        except (TypeError, ValueError):
                            urgency_str = str(urgency_val)
                    
                    with st.container(border=True):
                        picked_display = str(picked_date).strip() if picked_date else "N/A"
                        ticker_value = str(ticker).strip() if ticker else ""
                        if ticker_value:
                            star_count = max(1, len(ticker_value) - 1)
                            display_core = f"{ticker_value[0]}{'*' * star_count}(Picked: {picked_display})"
                        else:
                            display_core = f"(Picked: {picked_display})"
                        st.markdown(
                            f"<strong>{html.escape(display_core)}</strong> {html.escape(str(verdict))}",
                            unsafe_allow_html=True
                        )
                        st.caption(f"{signal}")
                        st.markdown(
                            f"<small>Urgency {urgency_str} | News {news}</small>",
                            unsafe_allow_html=True
                        )
                        
                        # Selection Button
                        btn_type = "primary" if is_selected else "secondary"
                        btn_label = "Selected ✓" if is_selected else "Select"
                        if st.button(btn_label, key=f"btn_{ticker}_{i}", use_container_width=True, type=btn_type):
                            st.session_state.focus_selected = ticker
                            st.rerun()

        # --- Detail Panel ---
        st.divider()
        st.markdown("### Detail Panel")
        
        selected_ticker = st.session_state.focus_selected
        selected_item = next((item for item in focus_items if item['ticker'] == selected_ticker), None)
        
        if selected_item:
            st.markdown("**Facts**")
            td = selected_item.get('trigger_details', {})
            st.caption(f"Signal: {td.get('trigger_type', 'N/A')}")
            st.caption(
                f"Price: ${float(td.get('current_price') or 0):.2f} | "
                f"Key Level: {td.get('key_level', 'N/A')}"
            )

            details_text = td.get('details', '')
            if details_text:
                st.text_area("Facts", value=str(details_text), height=100)
            else:
                st.caption("No trigger facts available for this ticker")

            st.markdown("**AI Judgement**")
            logic = selected_item.get('logic_pillars', {})

            # Check if logic actually contains data
            if logic and any(logic.values()):
                # Helper to clean text
                def clean_text(text):
                    cleaned = strip_evidence_refs(str(text)) if text is not None else ""
                    return cleaned or "N/A"

                tech = clean_text(logic.get('technical'))
                vol = clean_text(logic.get('volume_analysis'))
                news_catalyst = clean_text(logic.get('news_catalyst'))
                action = clean_text(selected_item.get('action_plan'))
                divergence = clean_text(selected_item.get('divergence'))

                st.caption(f"Technical: {tech}")
                st.caption(f"Volume: {vol}")
                st.caption(f"News: {news_catalyst}")

                if divergence and divergence != "N/A":
                    st.caption(f"Divergence: {divergence}")

                if action and action != "N/A":
                    if len(action) > 140:
                        action = action[:137] + "..."
                    st.caption(f"Action Plan: {action}")
            else:
                st.caption("No execution audit data saved for this ticker")

    else:
        # Dynamic Message from Snapshot
        focus_msg = meta.get("focus_message", "No active signals in Focus List.")
        st.info(focus_msg)

    st.divider()

    # --- 2. Alpha Picks Performance (Table) ---
    st.subheader("Alpha Picks Portfolio")
    
    raw_table = data.get("table_view_model", [])
    if raw_table:
        df = pd.DataFrame(raw_table)

        if 'picked_date' not in df.columns:
            df['picked_date'] = None
        
        # --- Strict Column Mapping from Dashboard.py ---
        # Rename columns to match the 'column_config' expectations
        # Order: Ticker, Price, Day%, Hold, Earnings, EMA21, EMA55, SMA200, RSI, ATR, Vol, Quant, Grades
        final_display = df[[
            'ticker', 'picked_date', 'last_price', 'Day%', 'hold_streak_days', 'earnings_fmt',
            'ema21_fmt', 'ema55_fmt', 'sma200_fmt', 'rsi14', 'atr14_pct', 'vol_ratio',
            'quant_rating_emoji', 'value_grade', 'growth_grade',
            'profitability_grade', 'momentum_grade', 'eps_revisions_grade'
        ]].rename(columns={
            'quant_rating_emoji': 'quant',
            'last_price': 'price',
            'earnings_fmt': 'earnings',
            'ema21_fmt': 'ema21',
            'ema55_fmt': 'ema55',
            'sma200_fmt': 'sma200',
            'rsi14_fmt': 'rsi14', # Map formatted RSI here
            'vol_ratio': 'vol'
        })

        final_display['ticker'] = final_display['ticker'].apply(mask_ticker)
        
        # Strict Config Copy from Dashboard.py
        if st.session_state.mobile_view:
             render_mobile_cards(final_display)
        else:
            st.dataframe(
                final_display,
                column_config={
                    'ticker': st.column_config.TextColumn('Ticker', width='small'),
                    'picked_date': st.column_config.TextColumn('Picked', width='small'),
                    'price': st.column_config.NumberColumn('Price', width='small', format='$%.2f'),
                    'Day%': st.column_config.NumberColumn('Day%', width='small', format='%.2f%%'),
                    'hold_streak_days': st.column_config.NumberColumn('Hold', width='small', format='%.0f'),
                    'earnings': st.column_config.TextColumn('Earnings', width='small'),
                    'ema21': st.column_config.TextColumn('EMA21', width='small'),
                    'ema55': st.column_config.TextColumn('EMA55', width='small'),
                    'sma200': st.column_config.TextColumn('SMA200', width='small'),
                    'rsi14': st.column_config.NumberColumn(
                        'RSI',
                        width='small',
                        format='%.0f',
                        help='>70 overbought, <30 oversold'
                    ),
                    'atr14_pct': st.column_config.NumberColumn('ATR%', width='small', format='%.1f%%'),
                    'vol': st.column_config.NumberColumn('Vol', width='small', format='%.1fx'),
                    'quant': st.column_config.TextColumn('Quant', width='small'),
                    'value_grade': st.column_config.TextColumn('Val', width='small'),
                    'growth_grade': st.column_config.TextColumn('Gro', width='small'),
                    'profitability_grade': st.column_config.TextColumn('Pro', width='small'),
                    'momentum_grade': st.column_config.TextColumn('Mom', width='small'),
                    'eps_revisions_grade': st.column_config.TextColumn('Rev', width='small')
                },
                width='stretch', # Updated to suppress deprecation warning
                hide_index=True,
                height=500
            )

    else:
        st.warning("No Portfolio Data Available.")

if __name__ == "__main__":
    main()
