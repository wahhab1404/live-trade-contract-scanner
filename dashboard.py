from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from bot import ContractSeries, SignalResult, UnderlyingContext, evaluate_contract, load_input


def build_dashboard_data(input_path: str, timeframe: str) -> dict[str, Any]:
    contracts, ctx = load_input(input_path)
    signals: list[SignalResult] = []

    for series in contracts:
        signal = evaluate_contract(series, ctx, timeframe)
        if signal:
            signals.append(signal)

    signals.sort(key=lambda x: x.score, reverse=True)

    companies: dict[str, dict[str, Any]] = {}
    for c in contracts:
        companies.setdefault(
            c.symbol,
            {"symbol": c.symbol, "contracts": 0, "call_count": 0, "put_count": 0},
        )
        companies[c.symbol]["contracts"] += 1
        if c.option_type == "CALL":
            companies[c.symbol]["call_count"] += 1
        else:
            companies[c.symbol]["put_count"] += 1

    return {
        "timeframe": timeframe,
        "underlying": ctx.symbol,
        "contracts_total": len(contracts),
        "signals_total": len(signals),
        "companies": list(companies.values()),
        "signals": [
            {
                "contract": s.contract,
                "score": s.score,
                "reasons": s.reasons,
                "timeframe": s.timeframe,
            }
            for s in signals
        ],
    }


def render_dashboard_html(data: dict[str, Any]) -> str:
    company_cards = "".join(
        f"""
        <div class=\"card\">
          <h3>{c['symbol']}</h3>
          <p>العقود: <b>{c['contracts']}</b></p>
          <p>CALL: {c['call_count']} | PUT: {c['put_count']}</p>
        </div>
        """
        for c in data["companies"]
    )

    signal_rows = "".join(
        f"""
        <tr>
          <td>{idx + 1}</td>
          <td>{s['contract']}</td>
          <td><span class=\"badge\">{s['score']}</span></td>
          <td>{'، '.join(s['reasons'])}</td>
          <td>{s['timeframe']}</td>
        </tr>
        """
        for idx, s in enumerate(data["signals"])
    )

    if not signal_rows:
        signal_rows = "<tr><td colspan='5'>لا توجد إشارات مطابقة حالياً</td></tr>"

    return f"""
<!DOCTYPE html>
<html lang=\"ar\" dir=\"rtl\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Live Trade Scanner Platform</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .hero {{ display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; }}
    .panel {{ background:#111827; border:1px solid #1f2937; border-radius:14px; padding:18px; }}
    .kpis {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap:12px; margin-top:16px; }}
    .kpi {{ background:#1e293b; border-radius:12px; padding:14px; }}
    .kpi small {{ color:#94a3b8; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px; margin-top:16px; }}
    .card {{ background:#1e293b; border-radius:12px; padding:14px; }}
    table {{ width:100%; border-collapse: collapse; margin-top:14px; font-size:14px; }}
    th,td {{ border-bottom:1px solid #334155; padding:12px; text-align:right; vertical-align:top; }}
    th {{ color:#93c5fd; }}
    .badge {{ background:#22c55e; color:#052e16; border-radius:999px; padding:3px 10px; font-weight:bold; }}
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"panel hero\">
      <div>
        <h1>منصة Live Trade Scanner</h1>
        <p>عرض احترافي للشركات، العقود، والصفقات المقترحة بأسلوب منصات التداول الحديثة.</p>
      </div>
      <div>
        <p>Underlying: <b>{data['underlying']}</b></p>
        <p>Timeframe: <b>{data['timeframe']}</b></p>
      </div>
    </div>

    <div class=\"kpis\">
      <div class=\"kpi\"><small>إجمالي العقود</small><h2>{data['contracts_total']}</h2></div>
      <div class=\"kpi\"><small>إجمالي الصفقات المقترحة</small><h2>{data['signals_total']}</h2></div>
    </div>

    <h2>الشركات المتابعة</h2>
    <div class=\"grid\">{company_cards}</div>

    <h2>الصفقات المقترحة</h2>
    <div class=\"panel\">
      <table>
        <thead><tr><th>#</th><th>العقد</th><th>Score</th><th>أسباب الإشارة</th><th>الفريم</th></tr></thead>
        <tbody>{signal_rows}</tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    data: dict[str, Any] = {}

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/data":
            payload = json.dumps(self.data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        html = render_dashboard_html(self.data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)


def main() -> None:
    parser = argparse.ArgumentParser(description="Professional options scanner dashboard")
    parser.add_argument("--input", default="sample_data.json", help="Path to JSON market data")
    parser.add_argument("--timeframe", default="1h", choices=["1h", "15m"])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8080, type=int)
    args = parser.parse_args()

    DashboardHandler.data = build_dashboard_data(args.input, args.timeframe)
    server = HTTPServer((args.host, args.port), DashboardHandler)

    print(f"Dashboard running on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
