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
    filter_txt = st.text_input(
        "Filter",
        key="mob_filter",
        placeholder="Filter ticker",
        label_visibility="collapsed"
    )
    sort_opt = st.selectbox(
        "Sort",
        ["Ticker A-Z", "Hold Desc"],
        key="mob_sort",
        label_visibility="collapsed"
    )

    # --- Logic ---
    # 1. Filter
    if filter_txt:
        needle = filter_txt.strip().upper()
        if needle:
            masked_match = df['ticker'].fillna('').astype(str).str.upper().str.contains(needle, regex=False)
            raw_col = df['ticker_raw'] if 'ticker_raw' in df.columns else df['ticker']
            raw_match = raw_col.fillna('').astype(str).str.upper().str.contains(needle, regex=False)
            df = df[masked_match | raw_match]
    
    # 2. Sort
    if sort_opt == "Ticker A-Z":
        sort_col = "ticker_raw" if "ticker_raw" in df.columns else "ticker"
        df = df.sort_values(by=sort_col, ascending=True)
    elif sort_opt == "Hold Desc":
        df = df.sort_values(by="hold_streak_days", ascending=False)

    def coerce_float(value):
        if value is None: return None
        if isinstance(value, str) and not value.strip(): return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def extract_float(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace(",", "")
            match = re.search(r"[-+]?\d*\.?\d+", cleaned)
            if match:
                try:
                    return float(match.group())
                except (TypeError, ValueError):
                    return None
        return None

    def format_signal_label(value):
        text = str(value or "").strip()
        if not text:
            return "Hold"
        return text

    # Iterate rows
    for index, row in df.iterrows():
        # Prepare Data
        ticker = row.get('ticker', 'N/A')
        ticker_safe = html.escape(str(ticker))
        # Check if ticker is masked logic or raw string
        # (Assuming 'ticker' col is already masked in main, but let's be safe)
        
        price_value = coerce_float(row.get('price'))
        signal = row.get('quant', 'Hold') # Using 'quant' emoji as signal or raw text
        signal_text = format_signal_label(signal)
        signal_safe = html.escape(signal_text)

        if price_value is None:
            price_display = "N/A"
        else:
            price_display = f"${price_value:.2f}"

        # Grades Visuals (Moved to Details, but fetched here)
        val = row.get('value_grade', '-')
        gro = row.get('growth_grade', '-')
        mom = row.get('momentum_grade', '-')
        pro = row.get('profitability_grade', '-')
        rev = row.get('eps_revisions_grade', '-')
        
        # Tech & Stats (Mini Summary)
        # Goal: RSI 60.00 · Vol 1.15x · :green[>E21] · :red[<S200]
        
        # 1. Helper for safe float
        def format_float(val, precision=2):
            f_val = extract_float(val)
            if f_val is None:
                return "-"
            return f"{f_val:.{precision}f}"

        rsi_val = format_float(row.get('rsi14', '-'))
        vol_val = format_float(row.get('vol', '-'))
        atr_pct = format_float(row.get('atr14_pct', '-')) # Not in mini summary but needed for logic if added
        rsi_detail = rsi_val
        vol_detail = vol_val
        atr_detail = atr_pct
        ema21_detail = format_float(row.get('ema21', '-'))
        ema55_detail = format_float(row.get('ema55', '-'))
        sma200_detail = format_float(row.get('sma200', '-'))
        
        # 2. Trend Logic
        # Need raw float for comparison
        raw_price = price_value # already float or None
        
        def safe_float(v):
            return extract_float(v)
             
        raw_e21 = safe_float(row.get('ema21'))
        raw_e55 = safe_float(row.get('ema55'))
        raw_s200 = safe_float(row.get('sma200'))
        
        trend_tags = []
        if raw_price is not None:
             if raw_e21 is not None:
                 if raw_price > raw_e21: trend_tags.append(":green[>E21]")
                 else: trend_tags.append(":red[<E21]")
             
             if raw_e55 is not None:
                 if raw_price > raw_e55: trend_tags.append(":green[>E55]")
                 else: trend_tags.append(":red[<E55]")
             
             if raw_s200 is not None:
                 if raw_price > raw_s200: trend_tags.append(":green[>S200]")
                 else: trend_tags.append(":red[<S200]")
        
        trend_str = " · ".join(trend_tags) if trend_tags else "Trend N/A"
        
        tech_line = f"RSI {rsi_val} · Vol {vol_val}x · {trend_str}"

        # Earnings: 2024-04-25 · Hold: 45d
        earning = row.get('earnings', '-')
        streak = row.get('hold_streak_days', '-')
        stats_line = f"Earn: {earning} · Hold: {streak}d"
        
        # Picked Date Formatting (Shorten: 2024-01-15 -> 01/15/24)
        pick_raw = row.get('picked_date', '')
        pick_display = ""
        if pick_raw:
             try:
                 # Try parse YYYY-MM-DD
                 d_obj = datetime.strptime(str(pick_raw).strip(), "%Y-%m-%d")
                 pick_display = d_obj.strftime("%m/%d/%y")
             except:
                 pick_display = str(pick_raw)

        # --- Render Card (Native) ---
        with st.container(border=True):
            # Row 1: Ticker + Picked | Quant (Top Right)
            c1, c2 = st.columns([0.72, 0.28])
            with c1:
                if pick_display:
                    st.markdown(
                        f"**{ticker_safe}** <span class='mobile-picked'> · Picked {pick_display}</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"**{ticker_safe}**")
            with c2:
                st.markdown(
                    f"<div class='mobile-quant'>{signal_safe}</div>",
                    unsafe_allow_html=True
                )
            
            # Row 2: Price
            st.markdown(
                f"<div class='mobile-price'>{price_display}</div>",
                unsafe_allow_html=True
            )

            # Row 3 & 4: Mini Summaries
            st.caption(tech_line)
            st.caption(stats_line)
            
            # Expander: Full Details
            with st.expander("Details"):
                # Grades Section
                st.caption("**Factor Grades**")
                g1, g2, g3, g4, g5 = st.columns(5)
                g1.write(f"Val {val}")
                g2.write(f"Gro {gro}")
                g3.write(f"Mom {mom}")
                g4.write(f"Pro {pro}")
                g5.write(f"Rev {rev}")
                
                st.divider()
                
                def format_trend_detail(label, value):
                    if value is None:
                        return f"{label}: N/A"
                    if raw_price is None:
                        return f"{label}: {value:.2f}"
                    if raw_price > value:
                        return f":green[>{label}: {value:.2f}]"
                    return f":red[<{label}: {value:.2f}]"

                ec1, ec2 = st.columns(2)
                with ec1:
                    st.caption("**Technical**")
                    st.write(f"RSI: {rsi_detail}")
                    st.write(f"Vol Ratio: {vol_detail}")
                    st.write(f"ATR%: {atr_detail}")
                with ec2:
                    st.caption("**Trend**")
                    st.markdown(format_trend_detail("EMA21", raw_e21))
                    st.markdown(format_trend_detail("EMA55", raw_e55))
                    st.markdown(format_trend_detail("SMA200", raw_s200))
                
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
    if '*' in value:
        return value
    value = value.upper()
    length = len(value)
    if length == 1:
        return f"{value[0]}*"
    if length == 2:
        return f"{value[0]}*"
    if length == 3:
        return f"{value[0]}**"
    return f"{value[0]}{'*' * (length - 2)}{value[-1]}"


def safe_float(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "")
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                return float(match.group())
            except (TypeError, ValueError):
                return None
    return None


def format_distance_pct(val) -> str:
    f_val = safe_float(val)
    if f_val is None:
        return "—"
    return f"{f_val:+.1f}%"


def format_catalyst_label(dte) -> str:
    f_val = safe_float(dte)
    if f_val is None:
        return "—"
    dte_int = int(f_val)
    if dte_int >= 0:
        return f"ER -{dte_int}d"
    return f"ER +{abs(dte_int)}d"


def resolve_trend_label(trend_color) -> str:
    color = str(trend_color or "").upper()
    if color == "GREEN":
        return "bullish"
    if color == "RED":
        return "bearish"
    return "neutral"


def format_tech_status(item: dict) -> str:
    trigger_key = str(item.get('primary_trigger_key') or '')
    line_label = 'SMA200'
    dist_val = item.get('dist_sma200_pct')
    if 'EMA55' in trigger_key:
        line_label = 'EMA55'
        dist_val = item.get('dist_ema55_pct')
    elif 'EMA21' in trigger_key:
        line_label = 'EMA21'
        dist_val = item.get('dist_ema21_pct')

    status = '—'
    f_dist = safe_float(dist_val)
    if f_dist is not None:
        status = 'below' if f_dist < 0 else 'above'
        status = f"{status} {line_label}"
    confirm_days = item.get('break_confirm_days')
    f_confirm = safe_float(confirm_days)
    if f_confirm is not None and f_confirm > 0 and status != '—':
        status = f"{status} ({int(f_confirm)}d)"
    return status


def determine_setup_label(item: dict) -> str:
    dte = safe_float(item.get('dte'))
    trigger_key = str(item.get('primary_trigger_key') or '')
    signal_text = str(item.get('signal') or '')
    volume_alert = bool(item.get('volume_alert')) if item.get('volume_alert') is not None else False
    news_raw = safe_float(item.get('news_sentiment_raw'))

    if dte is not None and 0 <= int(dte) <= 5:
        return 'IMMINENT_CATALYST'
    if 'EARNINGS' in trigger_key or 'Earnings' in signal_text:
        return 'IMMINENT_CATALYST'
    if volume_alert or 'VOLUME' in trigger_key or 'Volume' in signal_text:
        return 'VOL_MOMENTUM'
    if news_raw is not None and abs(news_raw) >= 0.6:
        return 'NEWS_SHOCK'
    if any(key in trigger_key for key in ['BREAK', 'SELL_RULE', 'GAP_DOWN']) or 'Break' in signal_text:
        return 'BREAK_RISK'
    return 'WATCH'


def format_urgency_news(urgency_val, news_raw) -> str:
    f_urgency = safe_float(urgency_val)
    if f_urgency is None:
        urgency_str = '—'
    else:
        urgency_str = f"{f_urgency:.0f}"
    if news_raw is None:
        news_str = '—'
    else:
        news_str = f"{news_raw:+.2f}"
    return f"{urgency_str} | News {news_str}"


def format_key_levels_line(item: dict) -> str:
    parts = []
    for label, level_key, dist_key in [
        ('SMA200', 'sma200', 'dist_sma200_pct'),
        ('EMA55', 'ema55', 'dist_ema55_pct'),
        ('EMA21', 'ema21', 'dist_ema21_pct')
    ]:
        level = safe_float(item.get(level_key))
        dist_val = safe_float(item.get(dist_key))
        if level is None or dist_val is None:
            continue
        parts.append(f"{label} {level:.2f} ({dist_val:+.1f}%)")
    return " | ".join(parts) if parts else '—'


def format_volume_evidence(vol_ratio) -> str:
    f_val = safe_float(vol_ratio)
    if f_val is None:
        return 'RVOL20 —'
    if f_val >= 2.0:
        note = 'volume confirms move'
    elif f_val >= 1.5:
        note = 'volume elevated'
    elif f_val < 1.0:
        note = 'volume light'
    else:
        note = 'volume neutral'
    return f"RVOL20 {f_val:.2f}x · {note}"


def format_news_evidence(item: dict) -> str:
    headline = item.get('news_headline')
    summary = item.get('news_summary')
    headline_age = item.get('news_age')
    source_count = item.get('news_sources')

    items = []
    if headline:
        if headline_age and source_count is not None:
            items.append(f"{headline} ({headline_age}, {source_count} src)")
        elif headline_age:
            items.append(f"{headline} ({headline_age})")
        else:
            items.append(str(headline))
    if summary and (not headline or summary.strip() not in str(headline)):
        items.append(str(summary))
    return " | ".join(items[:2]) if items else '—'


def build_one_line_verdict(item: dict) -> str:
    verdict = str(item.get('verdict') or 'WATCH').upper()
    trend_color = str(item.get('trend_color') or '').upper()

    verdict_prefix = {
        'EXIT': 'RISK_OFF / No Entry',
        'TRIM': 'RISK_OFF / No Entry',
        'ACCUMULATE': 'RISK_ON / Entry',
        'STRONG_ACCUMULATE': 'RISK_ON / Entry',
        'HIGH_RVOL_EVENT': 'RISK_OFF / Volatility Event',
        'RATING_PRESSURE': 'RISK_OFF / Rating Pressure',
        'EARNINGS_MOMO': 'RISK_ON / Event Momentum',
        'TREND_CONFIRMATION': 'RISK_ON / Trend Active',
        'SENTIMENT_COLLISION': 'NEUTRAL / Signal Conflict',
        'TREND_CONFLICT_UPG': 'NEUTRAL / Signal Conflict',
        'EVENT_WINDOW': 'NEUTRAL / Event Window'
    }

    if verdict in verdict_prefix:
        prefix = verdict_prefix[verdict]
    elif verdict in ['EXIT', 'TRIM']:
        prefix = 'RISK_OFF / No Entry'
    elif verdict in ['ACCUMULATE', 'STRONG_ACCUMULATE']:
        prefix = 'RISK_ON / Entry'
    elif trend_color == 'GREEN':
        prefix = 'RISK_ON / Trend Active'
    elif trend_color == 'RED':
        prefix = 'RISK_OFF / Trend Broken'
    else:
        prefix = 'NEUTRAL / Range Bound'

    dist_val = safe_float(item.get('dist_sma200_pct'))
    dist_label = 'price —'
    if dist_val is not None:
        side = 'below' if dist_val < 0 else 'above'
        dist_label = f"price {abs(dist_val):.1f}% {side} SMA200"
    catalyst = format_catalyst_label(item.get('dte'))
    trend = resolve_trend_label(item.get('trend_color'))
    if catalyst == '—':
        return f"{prefix} - {dist_label}, trend {trend}."
    return f"{prefix} - {catalyst} + {dist_label}, trend {trend}."



def format_verdict_label(value: str) -> str:
    text = str(value or "").replace("_", " ").strip()
    if not text:
        return "Watch"
    return text.lower().capitalize()


def format_picked_label(value: str) -> str:
    picked = str(value or "").strip()
    return picked if picked else "N/A"


def resolve_next_action(verdict: str, trend_color: str) -> str:
    verdict_action = {
        'EXIT': 'remove from focus / reduce exposure',
        'TRIM': 'remove from focus / reduce exposure',
        'ACCUMULATE': 'add alert / size up',
        'STRONG_ACCUMULATE': 'add alert / size up',
        'HIGH_RVOL_EVENT': 'watch only (volatility event)',
        'RATING_PRESSURE': 'watch only (wait for confirmation)',
        'SENTIMENT_COLLISION': 'watch only (wait for confirmation)',
        'TREND_CONFLICT_UPG': 'watch only (wait for confirmation)',
        'EARNINGS_MOMO': 'add alert / event follow-through',
        'EVENT_WINDOW': 'watch only (event risk window)',
        'TREND_CONFIRMATION': 'monitor for entry/add (active uptrend)'
    }
    if verdict in verdict_action:
        return verdict_action[verdict]
    if trend_color == 'GREEN':
        return 'monitor for entry/add (active uptrend)'
    if trend_color == 'RED':
        return 'watch only (wait for setup)'
    return 'watch only'


def format_ban_line(dte) -> str:
    if dte is None:
        return 'Ban: None (No immediate ER risk)'

    dte_int = int(dte)
    if 0 <= dte_int <= 5:
        return f'Ban: until ER passed + 2 sessions (DTE: {dte_int})'
    if -2 <= dte_int < 0:
        return f'Ban: cooling down post-ER (DTE: +{abs(dte_int)})'
    return 'Ban: None (No immediate ER risk)'


def build_focus_options(focus_items: list) -> tuple[list, dict]:
    options = []
    ticker_map = {}
    for item in focus_items:
        t_raw = item.get('ticker')
        if not t_raw:
            continue
        t_display = mask_ticker(t_raw)
        verdict_display = format_verdict_label(item.get('verdict', 'WATCH'))
        picked_display = format_picked_label(item.get('picked_date'))
        label = f"{t_display} | Picked {picked_display} | {verdict_display}"
        options.append(label)
        ticker_map[label] = t_raw
    return options, ticker_map

def main():
    data = load_data()
    if not data:
        st.error("System Offline: Snapshot missing.")
        return

    meta = data.get("meta", {})
    updated_at = meta.get("updated_at", "Unknown")

    if "mobile_view" not in st.session_state:
        st.session_state["mobile_view"] = False

    # Auto-Detect Mobile (Only runs once ideally, but Streamlit reruns might re-trigger)
    # We use session_state to hold the "auto-detected" preference once.
    if "first_load" not in st.session_state:
        is_mobile = is_mobile_device()
        # Only finalize state if we got a valid detection result (True/False), not None
        if is_mobile is not None:
            st.session_state["mobile_view"] = is_mobile
            st.session_state.first_load = True
            st.rerun()
        # If is_mobile is None, we do nothing this run.
        # Streamlit will likely rerun when st_javascript returns the value.

    # User requested removal of manual toggle to rely on auto-detection
    # use_mobile = st.toggle("📱 View", value=st.session_state.get("mobile_view", False), key="mobile_view_toggle")
    # st.session_state.mobile_view = use_mobile

    # --- Header ---
    if not st.session_state.get("mobile_view", False):
        st.title("Performance Overview")
        st.caption(f"Last Synced: {updated_at}")

    if not st.session_state.get("mobile_view", False):
        st.divider()

    # --- 1. Focus List (Interactive) ---
    if not st.session_state.get("mobile_view", False):
        st.markdown("### Focus List (Top 8)")
        st.caption("Scan format: Ticker | Setup | Tech | Distance | Catalyst | Urgency/News")
    
    focus_items = data.get("focus_view_model", [])
    
    if focus_items:
        ticker_list = [item.get('ticker') for item in focus_items if item.get('ticker')]
        if 'focus_selected' not in st.session_state or st.session_state.focus_selected not in ticker_list:
            if ticker_list:
                st.session_state.focus_selected = ticker_list[0]

        options, ticker_map = build_focus_options(focus_items)
        current_ticker = st.session_state.focus_selected
        default_index = 0
        for i, opt in enumerate(options):
            if ticker_map.get(opt) == current_ticker:
                default_index = i
                break

        if not options:
            st.info("No focus tickers available.")
            return

        if st.session_state.get("mobile_view", False):
            st.caption(f"Last Synced: {updated_at}")
            st.subheader("Key APs to watch")

        selected_label = st.selectbox(
            "Select Ticker to Deep Dive",
            options=options,
            index=default_index,
            key="focus_navigator",
            label_visibility="collapsed" if st.session_state.get("mobile_view", False) else "visible"
        )
        if selected_label:
            st.session_state.focus_selected = ticker_map[selected_label]

        scan_rows = []
        for item in focus_items:
            scan_rows.append({
                'Ticker': mask_ticker(item.get('ticker', '')),
                'Setup': determine_setup_label(item),
                'Tech': format_tech_status(item),
                'Distance': format_distance_pct(item.get('dist_sma200_pct')),
                'Catalyst': format_catalyst_label(item.get('dte')),
                'Urgency/News': format_urgency_news(item.get('urgency'), safe_float(item.get('news_sentiment_raw')))
            })

        scan_df = pd.DataFrame(scan_rows)
        st.dataframe(scan_df, use_container_width=True, hide_index=True)

        if not st.session_state.get("mobile_view", False):
            st.divider()

        selected_ticker = st.session_state.focus_selected
        selected_item = next((item for item in focus_items if item.get('ticker') == selected_ticker), None)

        if selected_item:
            latest_price = safe_float(selected_item.get('latest_price'))
            price_type = selected_item.get('price_type') or 'Close'
            price_timestamp = selected_item.get('price_timestamp') or '—'

            price_label = "N/A"
            if latest_price is not None:
                price_label = f"${latest_price:.2f} ({price_type}, {price_timestamp})"

            divergence_text = strip_evidence_refs(str(selected_item.get('divergence', '')))
            divergence_line = divergence_text if divergence_text else '—'

            st.markdown("### Deep Dive")
            st.markdown("**A) One-line Verdict**")
            st.write(build_one_line_verdict(selected_item))

            st.markdown("**B) Evidence**")
            st.caption(f"Price: {price_label}")
            st.caption(f"Key Levels: {format_key_levels_line(selected_item)}")
            st.caption(f"Volume: {format_volume_evidence(selected_item.get('vol_ratio'))}")
            st.caption(f"News: {format_news_evidence(selected_item)}")
            st.caption(f"Divergence: {divergence_line}")

            st.markdown("**C) Playbook**")
            dte = safe_float(selected_item.get('dte'))
            
            st.caption(format_ban_line(dte))

            # Dynamic Trigger Logic based on price vs EMAs/SMA
            dist_sma200 = safe_float(selected_item.get('dist_sma200_pct'))
            dist_ema21 = safe_float(selected_item.get('dist_ema21_pct'))
            
            if dist_sma200 is not None and dist_sma200 > 0 and dist_ema21 is not None and dist_ema21 > 0:
                # Strong Uptrend
                st.caption("Watch trigger (Primary): hold line above EMA21")
                st.caption("Watch trigger (Secondary): trend validation at SMA200")
                st.caption("Failure: loss of EMA21 with RVOL > 1")
            elif dist_sma200 is not None and dist_sma200 < 0:
                # Downtrend / Break
                st.caption("Watch trigger (Primary): strong close to reclaim SMA200")
                st.caption("Watch trigger (Secondary): 2 consecutive closes above EMA21")
                st.caption("Failure: reject at EMA21 with RVOL < 1")
            else:
                # Mixed / Near levels
                st.caption("Watch trigger (Primary): definitive break above nearest resistance")
                st.caption("Watch trigger (Secondary): establish higher low")
                st.caption("Failure: breakdown below recent consolidation")

            # Next action logic based on trend and verdict
            verdict = str(selected_item.get('verdict') or '').upper()
            trend_color = selected_item.get('trend_color', '').upper()
            st.caption(f"Next action: {resolve_next_action(verdict, trend_color)}")

            action_plan = selected_item.get('action_plan', '')
            if action_plan:
                action_clean = strip_evidence_refs(str(action_plan))
                if action_clean:
                    st.caption(f"Action plan note: {action_clean}")

            td = selected_item.get('trigger_details', {})
            if isinstance(td, dict) and td.get('details'):
                with st.expander("Trigger details", expanded=False):
                    st.write(str(td.get('details')))
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
        # Order: Ticker, Price, Hold, Earnings, EMA21, EMA55, SMA200, RSI, ATR, Vol, Quant, Grades
        expected_cols = [
            'ticker', 'picked_date', 'last_price', 'hold_streak_days', 'earnings_fmt',
            'ema21_fmt', 'ema55_fmt', 'sma200_fmt', 'rsi14', 'atr14_pct', 'vol_ratio',
            'quant_rating_emoji', 'value_grade', 'growth_grade',
            'profitability_grade', 'momentum_grade', 'eps_revisions_grade'
        ]

        final_display = df.reindex(columns=expected_cols).rename(columns={
            'quant_rating_emoji': 'quant',
            'last_price': 'price',
            'earnings_fmt': 'earnings',
            'ema21_fmt': 'ema21',
            'ema55_fmt': 'ema55',
            'sma200_fmt': 'sma200',
            'vol_ratio': 'vol'
        })

        ticker_raw = final_display['ticker'].fillna('').astype(str).str.strip().str.upper()
        final_display['ticker_raw'] = ticker_raw
        final_display['ticker'] = ticker_raw.apply(mask_ticker)
        
        # Strict Config Copy from Dashboard.py
        if st.session_state.get("mobile_view", False):
            render_mobile_cards(final_display)
        else:
            desktop_display = final_display.drop(columns=['ticker_raw'], errors='ignore')
            st.dataframe(
                desktop_display,
                column_config={
                    'ticker': st.column_config.TextColumn('Ticker', width='small'),
                    'picked_date': st.column_config.TextColumn('Picked', width='small'),
                    'price': st.column_config.NumberColumn('Price', width='small', format='$%.2f'),
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
                use_container_width=True,
                hide_index=True,
                height=500
            )

    else:
        st.warning("No Portfolio Data Available.")

if __name__ == "__main__":
    main()
