import streamlit as st
import requests
import json
from datetime import datetime
import zoneinfo

# --- Config ---
US_EASTERN_TZ = zoneinfo.ZoneInfo("America/New_York")

def is_mobile(user_agent: str) -> bool:
    """Detect if the user agent belongs to a mobile device."""
    if not user_agent:
        return False
    mobile_keywords = ['Android', 'webOS', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'Windows Phone']
    return any(keyword.lower() in user_agent.lower() for keyword in mobile_keywords)

def _upstash_request(cmds: list):
    """Execute a pipeline of commands via Upstash Redis REST API."""
    url = st.secrets.get("UPSTASH_REDIS_REST_URL")
    token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN")
    
    if not url or not token:
        return None
    
    try:
        # Upstash REST Pipeline format: [[cmd1], [cmd2], ...]
        resp = requests.post(
            f"{url}/pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json=cmds,
            timeout=3
        )
        return resp.json()
    except Exception:
        return None

def track_visit_once_per_session():
    """Tracks a visit exactly once per session. Fails open on errors."""
    if st.session_state.get("_av_tracked"):
        return

    try:
        # 1. Get Context
        ua = st.context.headers.get("user-agent", "")
        app_key = st.secrets.get("APP_ANALYTICS_KEY", "ap_public")
        today = datetime.now(US_EASTERN_TZ).strftime("%Y-%m-%d")
        
        # 2. Classify
        device_type = "mobile" if is_mobile(ua) else "desktop"
        
        # 3. Prepare Pipeline
        # We track:
        # - web:total, web:{date}
        # - {type}:total, {type}:{date}
        cmds = [
            ["INCR", f"visits:{app_key}:web:total"],
            ["INCR", f"visits:{app_key}:web:{today}"],
            ["INCR", f"visits:{app_key}:{device_type}:total"],
            ["INCR", f"visits:{app_key}:{device_type}:{today}"]
        ]
        
        # 4. Fire
        _upstash_request(cmds)
        
        # 5. Mark tracked
        st.session_state["_av_tracked"] = True
    except Exception:
        pass # Fail open

def get_stats():
    """Retrieve the required 6 metrics from Redis."""
    app_key = st.secrets.get("APP_ANALYTICS_KEY", "ap_public")
    
    # Generate date lists for day bucketing
    from datetime import timedelta
    now = datetime.now(US_EASTERN_TZ)
    last_7d = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    last_30d = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    
    # We need:
    # web_total (index 0)
    # mobile_total (index 1)
    # web daily keys (indices 2 to 31)
    # mobile daily keys (indices 32 to 61)
    
    cmds = [
        ["GET", f"visits:{app_key}:web:total"],
        ["GET", f"visits:{app_key}:mobile:total"]
    ]
    for d in last_30d:
        cmds.append(["GET", f"visits:{app_key}:web:{d}"])
    for d in last_30d:
        cmds.append(["GET", f"visits:{app_key}:mobile:{d}"])
        
    results = _upstash_request(cmds)
    
    if not results or not isinstance(results, list):
        return {k: "N/A" for k in ["mobile_7d", "mobile_30d", "mobile_total", "web_7d", "web_30d", "web_total"]}

    def parse_val(r):
        if r is None or "result" not in r: return 0
        try: return int(r["result"] or 0)
        except: return 0

    web_total = parse_val(results[0])
    mobile_total = parse_val(results[1])
    
    # Web slices
    web_daily = [parse_val(r) for r in results[2:32]]
    web_7d = sum(web_daily[:7])
    web_30d = sum(web_daily)
    
    # Mobile slices
    mobile_daily = [parse_val(r) for r in results[32:62]]
    mobile_7d = sum(mobile_daily[:7])
    mobile_30d = sum(mobile_daily)
    
    return {
        "mobile_7d": mobile_7d,
        "mobile_30d": mobile_30d,
        "mobile_total": mobile_total,
        "web_7d": web_7d,
        "web_30d": web_30d,
        "web_total": web_total
    }
