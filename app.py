import streamlit as st
import pandas as pd
import json
import os
import re
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
        return None # Return None to indicate "Loading/Unknown" - Do not default to False yet!
    mobile_keywords = ['Android', 'webOS', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'Windows Phone']
    return any(keyword in ua for keyword in mobile_keywords)

def render_mobile_cards(df):
    """Renders the Portfolio DataFrame as a vertical list of Native Streamlit Containers"""
    if df is None or df.empty:
        st.info("No Active Picks")
        return

    # --- Controls ---
    c_filter, c_sort = st.columns([0.6, 0.4])
    with c_filter:
        filter_txt = st.text_input("Filter Ticker", key="mob_filter", placeholder="e.g. NVDA")
    with c_sort:
        sort_opt = st.selectbox("Sort By", ["Day% Desc", "Ticker A-Z", "Hold Desc"], key="mob_sort", label_visibility="collapsed")

    # --- Logic ---
    # 1. Filter
    if filter_txt:
        df = df[df['ticker'].str.contains(filter_txt.upper(), na=False)]
    
    # 2. Sort
    if sort_opt == "Day% Desc":
        df = df.sort_values(by="Day%", ascending=False)
    elif sort_opt == "Ticker A-Z":
        df = df.sort_values(by="ticker", ascending=True)
    elif sort_opt == "Hold Desc":
        df = df.sort_values(by="hold_streak_days", ascending=False)

    def coerce_float(value):
        if value is None: return None
        if isinstance(value, str) and not value.strip(): return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # Iterate rows
    for index, row in df.iterrows():
        # Prepare Data
        ticker = row.get('ticker', 'N/A')
        # Check if ticker is masked logic or raw string
        # (Assuming 'ticker' col is already masked in main, but let's be safe)
        
        price_value = coerce_float(row.get('price'))
        day_pct_value = coerce_float(row.get('Day%'))
        signal = row.get('quant', 'Hold') # Using 'quant' emoji as signal or raw text

        if price_value is None:
            price_display = "N/A"
        else:
            price_display = f"${price_value:.2f}"

        # Color Logic for Day%
        if day_pct_value is None:
            pct_color = "gray"
            pct_str = "N/A"
            day_comp_str = "N/A"
        else:
            # Enhanced visual: text color instead of emoji icon
            if day_pct_value >= 0:
                day_comp_str = f":green[{day_pct_value:+.2f}%]"
            else:
                day_comp_str = f":red[{day_pct_value:+.2f}%]"

        # Grades Visuals (Moved to Details, but fetched here)
        val = row.get('value_grade', '-')
        gro = row.get('growth_grade', '-')
        mom = row.get('momentum_grade', '-')
        pro = row.get('profitability_grade', '-')
        rev = row.get('eps_revisions_grade', '-')
        
        # Tech & Stats (Mini Summary)
        # RSI 60 · Vol 1.1x · EMA21 175.5 · SMA200 150
        rsi = row.get('rsi14', '-')
        vol = row.get('vol', '-')
        ema21 = row.get('ema21', '-')
        sma200 = row.get('sma200', '-')
        
        tech_line = f"RSI {rsi} · Vol {vol}x · E21 {ema21} · S200 {sma200}"

        # Earnings: 2024-04-25 · Hold: 45d
        earning = row.get('earnings', '-')
        streak = row.get('hold_streak_days', '-')
        stats_line = f"Earn: {earning} · Hold: {streak}d"

        # --- Render Card (Native) ---
        with st.container(border=True):
            # Row 1: Ticker | Day%
            c1, c2 = st.columns([0.65, 0.35])
            with c1:
                st.markdown(f"**{ticker}**")
            with c2:
                st.markdown(f"<div style='text-align: right'>{day_comp_str}</div>", unsafe_allow_html=True)
            
            # Row 2: Price | Quant (Split to ensure clean separation)
            c3, c4 = st.columns([0.65, 0.35])
            with c3:
                 st.caption(f"{price_display}")
            with c4:
                 st.markdown(f"<div style='text-align: right'>{signal}</div>", unsafe_allow_html=True)

            # Row 3 & 4: Mini Summaries
            st.caption(tech_line)
            st.caption(stats_line)
            
            # Expander: Full Details
            with st.expander("Details"):
                # Grades Section
                st.caption("**Factor Grades**")
                g1, g2, g3, g4, g5 = st.columns(5)
                g1.write(f"Val\n**{val}**")
                g2.write(f"Gro\n**{gro}**")
                g3.write(f"Mom\n**{mom}**")
                g4.write(f"Pro\n**{pro}**")
                g5.write(f"Rev\n**{rev}**")
                
                st.divider()
                
                ec1, ec2 = st.columns(2)
                with ec1:
                   st.caption("**Technical**")
                   st.write(f"RSI: {rsi}")
                   st.write(f"Vol Ratio: {vol}")
                   st.write(f"ATR%: {row.get('atr14_pct', '-')}")
                with ec2:
                   st.caption("**Trend**")
                   st.write(f"EMA21: {ema21}")
                   st.write(f"EMA55: {row.get('ema55', '-')}")
                   st.write(f"SMA200: {sma200}")
                
                st.write(f"**Earnings**: {earning}")
                st.write(f"**Hold Streak**: {streak} Days")


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
            # Only finalize state if we got a valid detection result (True/False), not None
            if is_mobile is not None:
                st.session_state.mobile_view = is_mobile
                st.session_state.first_load = True
                st.rerun()
            # If is_mobile is None, we do nothing this run. 
            # Streamlit will likely rerun when st_javascript returns the value.
        
        # User requested removal of manual toggle to rely on auto-detection
        # use_mobile = st.toggle("📱 View", value=st.session_state.get("mobile_view", False), key="mobile_view_toggle")
        # st.session_state.mobile_view = use_mobile
    
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
             # --- Mobile Focus Navigator ---
             st.markdown("### Focus Navigator")
             
             # 1. Prepare Selectbox Options
             # Format: "AGX BUY" (Simplified)
             options = []
             ticker_map = {}
             
             for item in focus_items:
                 t_raw = item.get('ticker')
                 if not t_raw: continue
                 
                 # MASK TICKER
                 t_display = mask_ticker(t_raw)
                 
                 v = item.get('verdict', 'WATCH')
                 # Emoji for Verdict
                 v_icon = "🟢" if "BUY" in str(v).upper() else "👀"
                 
                 # Simple Label: "N*** 🟢 BUY"
                 label = f"{t_display} {v_icon} {v}"
                 options.append(label)
                 ticker_map[label] = t_raw # Map back to raw ticker for state
            
             # 2. State Management for Selectbox
             # Find current selection index
             current_ticker = st.session_state.focus_selected
             default_index = 0
             
             # Reverse lookup for index
             for i, opt in enumerate(options):
                 if ticker_map.get(opt) == current_ticker:
                     default_index = i
                     break
            
             selected_label = st.selectbox(
                 "Select Ticker to Deep Dive",
                 options=options,
                 index=default_index,
                 key="focus_navigator_mobile",
                 label_visibility="collapsed"
             )
             
             # Update State immediately
             if selected_label:
                 st.session_state.focus_selected = ticker_map[selected_label]

             # 3. Now Viewing Anchor
             # "One glance" summary container
             selected_item = next((i for i in focus_items if i['ticker'] == st.session_state.focus_selected), None)
             
             if selected_item:
                 with st.container(border=True):
                     # Top Row: Ticker + Verdict
                     t_str = selected_item.get('ticker')
                     v_str = selected_item.get('verdict')
                     u_raw = selected_item.get('urgency')
                     s_raw = selected_item.get('signal')
                     d_raw = selected_item.get('picked_date')
                     
                     st.markdown(f"**{t_str}**  |  {v_str}")
                     st.caption(f"Urgency {u_raw} · {s_raw} · {d_raw}")

             # Optional: Scan List Expander
             with st.expander("Show Full Focus List (Scan Mode)"):
                 for item in focus_items:
                     it_t = item.get('ticker')
                     it_v = item.get('verdict')
                     it_u = item.get('urgency')
                     st.caption(f"**{it_t}** ({it_v}) - Urgency {it_u}")


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

        # --- Deep Dive (Execution Dashboard) ---
        st.divider()
        # st.markdown("### Detail Panel") # Removed header to save space on mobile? Or keep for clarity? User said "Deep Dive".
        
        selected_ticker = st.session_state.focus_selected
        selected_item = next((item for item in focus_items if item['ticker'] == selected_ticker), None)
        
        if selected_item:
            td = selected_item.get('trigger_details', {})
            logic = selected_item.get('logic_pillars', {})
            
            # --- A) Setup Card ---
            with st.container(border=True):
                trig_type = td.get('trigger_type', 'N/A')
                st.markdown(f"**Setup** · {trig_type}")
                
                # Metrics (Simplified: Price Only)
                curr_price = float(td.get('current_price') or 0)
                
                # Single Metric
                st.metric("Price", f"${curr_price:.2f}")
                
                # Setup Details
                raw_details = str(td.get('details', 'No details available.'))
                # 200 char summary
                summary_details = (raw_details[:200] + '...') if len(raw_details) > 200 else raw_details
                st.caption(summary_details)
                if len(raw_details) > 200:
                    with st.expander("Show full setup details"):
                        st.write(raw_details)

            # --- B) Action Plan Card ---
            action_raw = selected_item.get('action_plan') or logic.get('action_plan')
            if action_raw:
                action_clean = strip_evidence_refs(str(action_raw))
                with st.container(border=True):
                    st.markdown("**AI Judgement** · Action Plan")
                    
                    act_summary = (action_clean[:250] + '...') if len(action_clean) > 250 else action_clean
                    st.write(act_summary)
                    
                    if len(action_clean) > 250:
                        with st.expander("Show full Action Plan"):
                            st.write(action_clean)

            # --- C) Logic Pillars (Tabs) ---
            t_tech, t_vol, t_news, t_div = st.tabs(["Technical", "Volume", "News", "Divergence"])
            
            def clean_text_safe(val):
                if not val: return "N/A"
                return strip_evidence_refs(str(val))

            with t_tech:
                st.write(clean_text_safe(logic.get('technical')))
            with t_vol:
                st.write(clean_text_safe(logic.get('volume_analysis')))
            with t_news:
                st.write(clean_text_safe(logic.get('news_catalyst')))
            with t_div:
                div_val = selected_item.get('divergence')
                st.write(clean_text_safe(div_val))
            
        else:
            st.info("Select a ticker to view details.")

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
