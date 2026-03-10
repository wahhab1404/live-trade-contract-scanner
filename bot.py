from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from statistics import mean
from typing import List, Optional


@dataclass
class Candle:
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class ContractSeries:
    symbol: str
    strike: float
    option_type: str  # CALL | PUT
    candles: List[Candle]


@dataclass
class UnderlyingContext:
    symbol: str
    stock_buy_volume: int
    stock_sell_volume: int


@dataclass
class SignalResult:
    contract: str
    score: float
    reasons: List[str]
    timeframe: str


def rsi(closes: List[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = mean(gains[-period:])
    avg_loss = mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def is_doji(c: Candle, ratio: float = 0.15) -> bool:
    body = abs(c.close - c.open)
    range_ = max(c.high - c.low, 1e-6)
    return body / range_ <= ratio


def is_hammer(c: Candle) -> bool:
    body = abs(c.close - c.open)
    lower_shadow = min(c.open, c.close) - c.low
    upper_shadow = c.high - max(c.open, c.close)
    return lower_shadow >= body * 2 and upper_shadow <= body


def narrow_sideways(candles: List[Candle], lookback: int = 8, max_width: float = 0.20) -> bool:
    if len(candles) < lookback:
        return False
    sample = candles[-lookback:]
    hi = max(c.high for c in sample)
    lo = min(c.low for c in sample)
    return (hi - lo) <= max_width


def deep_price_zone(last_price: float) -> bool:
    return (0.18 <= last_price <= 1.50) or (0.25 <= last_price <= 1.20)


def liquidity_tower(candles: List[Candle], min_volume: int = 1500) -> Optional[int]:
    if not candles:
        return None
    max_vol = max(c.volume for c in candles)
    if max_vol < min_volume:
        return None
    for i in range(len(candles) - 1, -1, -1):
        if candles[i].volume == max_vol:
            return i
    return None


def rsi_divergence(candles: List[Candle]) -> bool:
    if len(candles) < 20:
        return False
    closes = [c.close for c in candles]
    midpoint = len(closes) // 2
    rsi_1 = rsi(closes[:midpoint])
    rsi_2 = rsi(closes)
    if rsi_1 is None or rsi_2 is None:
        return False
    price_low_1 = min(closes[:midpoint])
    price_low_2 = min(closes[midpoint:])
    return price_low_2 <= price_low_1 and rsi_2 > rsi_1


def liquidity_break_and_reclaim(candles: List[Candle], tower_idx: int) -> bool:
    if tower_idx >= len(candles) - 2:
        return False
    tower_low = candles[tower_idx].low
    after = candles[tower_idx + 1 :]
    broke = any(c.low < tower_low for c in after)
    reclaimed = after[-1].close > tower_low
    return broke and reclaimed


def fake_liquidity_filter(option_type: str, contract_volume: int, ctx: UnderlyingContext) -> bool:
    if option_type != "PUT":
        return True
    net_stock_buy = ctx.stock_buy_volume - ctx.stock_sell_volume
    if contract_volume > 3000 and net_stock_buy > 5 * contract_volume:
        return False
    return True


def evaluate_contract(series: ContractSeries, ctx: UnderlyingContext, timeframe: str) -> Optional[SignalResult]:
    candles = series.candles
    if len(candles) < 10:
        return None

    last = candles[-1]
    reasons = []
    score = 0.0

    if deep_price_zone(last.close):
        score += 1.0
        reasons.append("السعر ضمن نطاق العقود المنخفضة")

    if narrow_sideways(candles):
        score += 1.2
        reasons.append("مسار عرضي ضيق (10-20 سنت)")

    if any(is_doji(c) for c in candles[-6:]):
        score += 1.0
        reasons.append("وجود شمعة دوجي")

    tower_idx = liquidity_tower(candles)
    if tower_idx is not None:
        score += 1.6
        reasons.append("برج سيولة 1500+")

        if liquidity_break_and_reclaim(candles, tower_idx):
            score += 1.1
            reasons.append("كسر قاع شمعة السيولة ثم ارتداد")

    if rsi_divergence(candles):
        score += 0.8
        reasons.append("دايفرجنس RSI إيجابي")

    if is_hammer(last):
        score += 0.4
        reasons.append("شمعة هامر")

    if not fake_liquidity_filter(series.option_type, last.volume, ctx):
        score -= 1.3
        reasons.append("تحذير: سيولة محتملة للتحوط")

    if series.option_type == "CALL":
        score += 0.2

    if score < 3.0:
        return None

    return SignalResult(
        contract=f"{series.symbol} {series.option_type} {series.strike}",
        score=round(score, 2),
        reasons=reasons,
        timeframe=timeframe,
    )


def load_input(path: str) -> tuple[List[ContractSeries], UnderlyingContext]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    contracts = []
    for item in payload["contracts"]:
        candles = [Candle(**c) for c in item["candles"]]
        contracts.append(
            ContractSeries(
                symbol=item["symbol"],
                strike=item["strike"],
                option_type=item["option_type"],
                candles=candles,
            )
        )

    ctx = UnderlyingContext(**payload["underlying_context"])
    return contracts, ctx


def main() -> None:
    parser = argparse.ArgumentParser(description="Option liquidity tower scanner")
    parser.add_argument("--input", required=True, help="Path to JSON market data")
    parser.add_argument("--timeframe", default="1h", choices=["1h", "15m"])
    args = parser.parse_args()

    contracts, ctx = load_input(args.input)

    results = []
    for series in contracts:
        signal = evaluate_contract(series, ctx, args.timeframe)
        if signal:
            results.append(signal)

    results.sort(key=lambda x: x.score, reverse=True)

    if not results:
        print("لا توجد إشارة مطابقة الآن.")
        return

    print("أفضل الإشارات:")
    for s in results:
        print(f"- {s.contract} | score={s.score} | tf={s.timeframe}")
        for reason in s.reasons:
            print(f"  • {reason}")


if __name__ == "__main__":
    main()
