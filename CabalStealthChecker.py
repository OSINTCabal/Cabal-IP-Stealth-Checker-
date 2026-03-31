#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        CABAL STEALTH CHECKER  //  osintcabal.org             ║
║        proxycheck.io v3 API  //  IP Intelligence             ║
╚══════════════════════════════════════════════════════════════╝

Detect proxies, VPNs, TOR exits, hosting IPs, and scrapers
using the proxycheck.io v3 API. Free tier supported.

Usage:
    python3 CabalStealthChecker.py
    python3 CabalStealthChecker.py <ip_address>
    python3 CabalStealthChecker.py --bulk

Setup:
    1. Get a free API key at https://proxycheck.io
    2. Set your key in one of two ways:
       a) Environment variable:  export PROXYCHECK_API_KEY="your_key_here"
       b) Create a .env file with: PROXYCHECK_API_KEY=your_key_here
          and pip install python-dotenv
    3. Run the script
"""

import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import re
import os
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.environ.get("PROXYCHECK_API_KEY", "")

if not API_KEY:
    print("\n  [!] ERROR: No API key found.")
    print("  [>] Set the PROXYCHECK_API_KEY environment variable or add it to a .env file.")
    print("  [>] Get a free key at: https://proxycheck.io\n")
    sys.exit(1)

API_BASE = "https://proxycheck.io/v3"
DAYS     = 30   # look-back window for detections (change freely)

# ─── ANSI COLORS ──────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    BLACK   = "\033[30m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"

    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"
    BG_DARK   = "\033[40m"


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(f"""{C.MAGENTA}{C.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║  {C.CYAN}  ██████╗ █████╗ ██████╗  █████╗ ██╗     {C.MAGENTA}                      ║
║  {C.CYAN} ██╔════╝██╔══██╗██╔══██╗██╔══██╗██║     {C.MAGENTA}                      ║
║  {C.CYAN} ██║     ███████║██████╔╝███████║██║     {C.MAGENTA}  STEALTH CHECKER      ║
║  {C.CYAN} ██║     ██╔══██║██╔══██╗██╔══██╗██║     {C.MAGENTA}  proxycheck.io v3     ║
║  {C.CYAN} ╚██████╗██║  ██║██████╔╝██║  ██║███████╗{C.MAGENTA}  IP Intelligence      ║
║  {C.CYAN}  ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝{C.MAGENTA}                     ║
║  {C.DIM}  osintcabal.org  //  OSINT Cabal Toolkit{C.MAGENTA}                        ║
╚══════════════════════════════════════════════════════════════════╝{C.RESET}
""")


def divider(label="", char="─", width=66, color=C.DIM):
    if label:
        pad = width - len(label) - 4
        left = pad // 2
        right = pad - left
        print(f"{color}{char * left}  {C.BOLD}{C.WHITE}{label}{C.RESET}{color}  {char * right}{C.RESET}")
    else:
        print(f"{color}{char * width}{C.RESET}")


def validate_ip(ip_str):
    ipv4 = re.compile(
        r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
    )
    ipv6 = re.compile(r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$')
    return bool(ipv4.match(ip_str) or ipv6.match(ip_str))


def colorize_risk(score):
    if score is None:
        return f"{C.DIM}N/A{C.RESET}"
    score = int(score)
    bar_len = 30
    filled = int((score / 100) * bar_len)
    if score <= 25:
        col = C.GREEN
        label = "LOW"
    elif score <= 50:
        col = C.YELLOW
        label = "MODERATE"
    elif score <= 75:
        col = C.RED
        label = "HIGH"
    else:
        col = f"{C.BOLD}{C.RED}"
        label = "CRITICAL"
    bar = f"{col}{'█' * filled}{C.DIM}{'░' * (bar_len - filled)}{C.RESET}"
    return f"{bar}  {col}{C.BOLD}{score}/100  [{label}]{C.RESET}"


def bool_badge(val):
    """YES = green, NO = red, always."""
    if val is True:
        return f"{C.BOLD}{C.GREEN}✔  YES{C.RESET}"
    elif val is False:
        return f"{C.BOLD}{C.RED}✘  NO{C.RESET}"
    else:
        return f"{C.DIM}?  UNKNOWN{C.RESET}"


def fmt_val(val, color=C.WHITE):
    if val is None:
        return f"{C.DIM}null{C.RESET}"
    return f"{color}{val}{C.RESET}"


def fmt_dt(iso_str):
    if not iso_str:
        return f"{C.DIM}null{C.RESET}"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return f"{C.CYAN}{dt.strftime('%Y-%m-%d  %H:%M:%S UTC')}{C.RESET}"
    except Exception:
        return f"{C.CYAN}{iso_str}{C.RESET}"


def row(label, value, label_width=28):
    print(f"  {C.DIM}{label:<{label_width}}{C.RESET}  {value}")


# ─── API CALL ─────────────────────────────────────────────────────────────────
def query_ip(ip):
    params = urllib.parse.urlencode({
        "key":  API_KEY,
        "days": DAYS,
        "ver":  "20-November-2025",
    })
    url = f"{API_BASE}/{ip}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw), url
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return json.loads(body), url
        except Exception:
            return {"status": "error", "message": str(e)}, url
    except Exception as e:
        return {"status": "error", "message": str(e)}, url


# ─── RENDER RESULT ────────────────────────────────────────────────────────────
def render(ip, data):
    status = data.get("status", "error")
    msg    = data.get("message", "")

    print()
    divider(f"  {ip}  ", char="═", color=C.MAGENTA)

    if status == "ok":
        status_str = f"{C.BOLD}{C.GREEN}✔  OK{C.RESET}"
    elif status == "warning":
        status_str = f"{C.BOLD}{C.YELLOW}⚠  WARNING — {msg}{C.RESET}"
    elif status == "denied":
        status_str = f"{C.BOLD}{C.RED}✘  DENIED — {msg}{C.RESET}"
    else:
        status_str = f"{C.BOLD}{C.RED}✘  ERROR — {msg}{C.RESET}"

    row("API Status", status_str)

    ip_data = data.get(ip)
    if not ip_data:
        print(f"\n  {C.RED}No data returned for {ip}.{C.RESET}\n")
        return

    # ── DETECTIONS ──────────────────────────────────────────────────────────
    det = ip_data.get("detections")
    if det and isinstance(det, dict):
        print()
        divider("DETECTIONS")
        row("Anonymous",   bool_badge(det.get("anonymous")))
        row("Proxy",       bool_badge(det.get("proxy")))
        row("VPN",         bool_badge(det.get("vpn")))
        row("TOR",         bool_badge(det.get("tor")))
        row("Hosting",     bool_badge(det.get("hosting")))
        row("Scraper",     bool_badge(det.get("scraper")))

        confidence = det.get("confidence")
        if confidence is not None:
            row("Confidence", colorize_risk(confidence))

        first_seen = det.get("first_seen")
        last_seen  = det.get("last_seen")
        if first_seen:
            row("First Seen", fmt_dt(first_seen))
        if last_seen:
            row("Last Seen",  fmt_dt(last_seen))

        det_type = det.get("type")
        if det_type:
            row("Detection Type", fmt_val(det_type, C.YELLOW))

    # ── NETWORK ─────────────────────────────────────────────────────────────
    net = ip_data.get("network")
    if net and isinstance(net, dict):
        net_fields = {
            "ASN":          (net.get("asn"),          C.CYAN),
            "Range":        (net.get("range"),        C.CYAN),
            "Hostname":     (net.get("hostname"),     C.WHITE),
            "Provider":     (net.get("provider"),     C.WHITE),
            "Organisation": (net.get("organisation"), C.WHITE),
            "Network Type": (net.get("type"),         C.YELLOW),
        }
        populated = {k: v for k, v in net_fields.items() if v[0] is not None}
        if populated:
            print()
            divider("NETWORK")
            for label, (val, color) in populated.items():
                row(label, fmt_val(val, color))

    # ── OPERATOR ────────────────────────────────────────────────────────────
    op = ip_data.get("operator")
    if op and isinstance(op, dict):
        print()
        divider("OPERATOR / VPN SERVICE")

        if op.get("name"):
            row("Name",       fmt_val(op.get("name"),       C.WHITE))
        if op.get("url"):
            row("URL",        fmt_val(op.get("url"),        C.CYAN))
        if op.get("anonymity"):
            row("Anonymity",  fmt_val(op.get("anonymity"),  C.YELLOW))
        if op.get("popularity"):
            row("Popularity", fmt_val(op.get("popularity"), C.YELLOW))

        services = op.get("services")
        if services:
            row("Services", fmt_val(", ".join(services), C.YELLOW))

        protocols = op.get("protocols")
        if protocols:
            row("Protocols", fmt_val(", ".join(protocols), C.DIM))

        add_ops = op.get("additional_operators")
        if add_ops and isinstance(add_ops, list):
            row("Additional Operators", fmt_val(", ".join(add_ops), C.DIM))

        # ── OPERATOR POLICIES ────────────────────────────────────────────
        policies = op.get("policies")
        if policies and isinstance(policies, dict):
            populated_policies = {k: v for k, v in policies.items() if v is not None}
            if populated_policies:
                print()
                divider("OPERATOR POLICIES", char="·", color=C.DIM)
                for k, v in populated_policies.items():
                    label = k.replace("_", " ").title()
                    if isinstance(v, bool):
                        row(label, bool_badge(v))
                    else:
                        row(label, fmt_val(str(v), C.WHITE))

    print()
    divider(char="═", color=C.MAGENTA)
    print(f"  {C.DIM}Lookup window: last {DAYS} days  //  proxycheck.io v3  //  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}{C.RESET}")
    print()


# ─── MULTI-IP SUMMARY TABLE ───────────────────────────────────────────────────
def summary_table(results):
    print()
    divider("BULK SCAN SUMMARY", char="═", color=C.MAGENTA)
    header = f"  {'IP Address':<20} {'Risk':>5}  {'Anon':>5}  {'Proxy':>5}  {'VPN':>4}  {'TOR':>4}  {'Country':<18}  {'Provider'}"
    print(f"{C.BOLD}{C.WHITE}{header}{C.RESET}")
    divider()
    for ip, data in results.items():
        ip_data = data.get(ip, {})
        det  = ip_data.get("detections", {})
        net  = ip_data.get("network", {})
        loc  = ip_data.get("location", {})
        risk = ip_data.get("risk", "?")

        def flag(val):
            if val is True:  return f"{C.GREEN}YES{C.RESET}"
            if val is False: return f"{C.RED}NO{C.RESET} "
            return f"{C.DIM}?  {C.RESET}"

        risk_col = C.GREEN if isinstance(risk, int) and risk <= 25 else \
                   C.YELLOW if isinstance(risk, int) and risk <= 50 else C.RED
        risk_str = f"{risk_col}{risk:>3}{C.RESET}" if isinstance(risk, int) else f"{C.DIM} ?{C.RESET}"

        country  = (loc.get("country") or "")[:17]
        provider = (net.get("provider") or "")[:30]

        print(f"  {C.CYAN}{ip:<20}{C.RESET} {risk_str}   "
              f"{flag(det.get('anonymous'))}   "
              f"{flag(det.get('proxy'))}   "
              f"{flag(det.get('vpn'))}  "
              f"{flag(det.get('tor'))}  "
              f"{C.WHITE}{country:<18}{C.RESET}  {C.DIM}{provider}{C.RESET}")
    divider(char="═", color=C.MAGENTA)
    print()


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    clear()
    banner()

    bulk_mode = "--bulk" in sys.argv
    cli_ips   = [a for a in sys.argv[1:] if not a.startswith("--")]

    if bulk_mode:
        print(f"  {C.CYAN}BULK MODE  {C.DIM}— enter IPs one per line, blank line when done{C.RESET}\n")
        ips = []
        while True:
            try:
                entry = input(f"  {C.DIM}IP> {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not entry:
                break
            if validate_ip(entry):
                ips.append(entry)
            else:
                print(f"  {C.YELLOW}⚠  Skipping invalid IP: {entry}{C.RESET}")

        if not ips:
            print(f"\n  {C.RED}No valid IPs entered.{C.RESET}\n")
            sys.exit(1)

        print(f"\n  {C.DIM}Scanning {len(ips)} IP(s)...{C.RESET}\n")
        bulk_results = {}
        for ip in ips:
            print(f"  {C.DIM}→ querying {ip} ...{C.RESET}", end="\r")
            result, _ = query_ip(ip)
            bulk_results[ip] = result
            render(ip, result)

        summary_table(bulk_results)

    else:
        if cli_ips:
            ip = cli_ips[0]
        else:
            try:
                ip = input(f"  {C.CYAN}Enter target IP address: {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n  {C.DIM}Aborted.{C.RESET}\n")
                sys.exit(0)

        if not ip:
            print(f"\n  {C.RED}No IP provided.{C.RESET}\n")
            sys.exit(1)

        if not validate_ip(ip):
            print(f"\n  {C.YELLOW}⚠  '{ip}' doesn't look like a valid IP address. Querying anyway...{C.RESET}\n")

        print(f"\n  {C.DIM}Querying proxycheck.io for {C.CYAN}{ip}{C.DIM} ...{C.RESET}\n")
        result, url = query_ip(ip)
        render(ip, result)

        while True:
            try:
                again = input(f"  {C.DIM}Check another IP? [y/N]: {C.RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if again != "y":
                break
            try:
                ip = input(f"  {C.CYAN}Enter target IP address: {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not ip:
                continue
            print(f"\n  {C.DIM}Querying ...{C.RESET}\n")
            result, url = query_ip(ip)
            render(ip, result)

    print(f"  {C.MAGENTA}[ OSINT Cabal  //  osintcabal.org ]{C.RESET}\n")


if __name__ == "__main__":
    main()
