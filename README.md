# 🕵️ Cabal Stealth Checker

**IP Intelligence via [proxycheck.io v3](https://proxycheck.io)**  
*An OSINT Cabal tool // [osintcabal.org](https://osintcabal.org)*

---

Cabal Stealth Checker is a terminal-based IP intelligence tool that detects whether a target IP address belongs to a proxy, VPN, TOR exit node, hosting provider, or known scraper network. Built for OSINT investigators, threat analysts, and researchers who need fast, no-nonsense IP attribution from the command line.

```
╔══════════════════════════════════════════════════════════════════╗
║    ██████╗ █████╗ ██████╗  █████╗ ██╗                           ║
║   ██╔════╝██╔══██╗██╔══██╗██╔══██╗██║                           ║
║   ██║     ███████║██████╔╝███████║██║     STEALTH CHECKER        ║
║   ██║     ██╔══██║██╔══██╗██╔══██╗██║     proxycheck.io v3       ║
║   ╚██████╗██║  ██║██████╔╝██║  ██║███████╗IP Intelligence        ║
║    ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝                     ║
║    osintcabal.org  //  OSINT Cabal Toolkit                       ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Features

- **Proxy / VPN / TOR detection** — instant yes/no flags with confidence scoring
- **Hosting & scraper identification** — flag datacenter and bot IPs
- **Operator intel** — VPN service name, protocols, anonymity level, no-log policies
- **Network context** — ASN, IP range, hostname, organization
- **Visual risk meter** — color-coded confidence bar (LOW → CRITICAL)
- **Bulk scan mode** — feed a list of IPs, get a summary table
- **CLI-friendly** — pipe IPs in, pass as arguments, or use interactive mode
- **Zero heavy dependencies** — pure Python stdlib, optional `.env` support

---

## Requirements

- Python 3.7+
- A free [proxycheck.io](https://proxycheck.io) API key
- `python-dotenv` *(optional, for `.env` file support)*

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/CabalStealthChecker.git
cd CabalStealthChecker

# Optional: install dotenv support for .env key loading
pip install python-dotenv
# or
pip install -r requirements.txt
```

---

## API Key Setup

Get a **free** API key at [https://proxycheck.io](https://proxycheck.io).  
The free tier allows **100 queries/day** without an account, or **1,000/day** with a free account.

### Option A — `.env` file *(recommended)*

```bash
cp .env.example .env
# Edit .env and paste your key:
# PROXYCHECK_API_KEY=your_key_here
```

### Option B — Environment variable

```bash
# Linux / macOS
export PROXYCHECK_API_KEY="your_key_here"

# Windows CMD
set PROXYCHECK_API_KEY=your_key_here

# Windows PowerShell
$env:PROXYCHECK_API_KEY="your_key_here"
```

> ⚠️ **Never hardcode your API key in the script. Never commit `.env` to git.**  
> `.env` is already in `.gitignore` — keep it that way.

---

## Usage

### Interactive mode
```bash
python3 CabalStealthChecker.py
```

### Single IP via argument
```bash
python3 CabalStealthChecker.py 1.2.3.4
```

### Bulk mode — enter multiple IPs interactively
```bash
python3 CabalStealthChecker.py --bulk
```

Bulk mode collects IPs one per line, then runs all lookups and prints a summary table at the end.

---

## Output Example

```
══════════════════════  185.220.101.45  ══════════════════════

  API Status                    ✔  OK

──────────────────────  DETECTIONS  ──────────────────────────
  Anonymous                     ✔  YES
  Proxy                         ✘  NO
  VPN                           ✘  NO
  TOR                           ✔  YES
  Hosting                       ✘  NO
  Scraper                       ✘  NO
  Confidence                    ████████████████░░░░░░░░░░░░░░  55/100  [MODERATE]
  First Seen                    2024-01-15  03:22:11 UTC
  Detection Type                TOR

──────────────────────  NETWORK  ─────────────────────────────
  ASN                           AS205100
  Hostname                      no-reverse-dns-set.com
  Provider                      F3 Netze e.V.
  Network Type                  hosting

──────────────────────  OPERATOR / VPN SERVICE  ──────────────
  Name                          Tor Project
  Anonymity                     High
```

---

## Configuration

You can adjust the detection look-back window at the top of the script:

```python
DAYS = 30   # look-back window in days — increase for longer history
```

---

## Free Tier Limits

| Tier | Daily Queries | Requires Account |
|------|--------------|-----------------|
| No key | 100/day | No |
| Free account | 1,000/day | Yes (free) |
| Paid plans | 10,000+/day | Yes |

Register free at [https://proxycheck.io](https://proxycheck.io).

---

## Part of the OSINT Cabal Toolkit

This tool is part of a growing suite of open-source OSINT utilities developed under the **OSINT Cabal** brand.

- 🌐 [osintcabal.org](https://osintcabal.org)
- 🔎 Counter-extremism research // Public records resources // OSINT tooling

---

## Disclaimer

This tool is intended for **lawful, ethical OSINT research** only. Use in accordance with applicable laws and the [proxycheck.io Terms of Service](https://proxycheck.io/terms/). The author assumes no liability for misuse.

---

## License

MIT License — see `LICENSE` for details.
