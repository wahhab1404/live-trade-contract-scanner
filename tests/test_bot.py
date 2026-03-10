from bot import Candle, narrow_sideways, is_doji, liquidity_tower


def test_narrow_sideways_true():
    candles = [
        Candle("t", 0.5, 0.58, 0.44, 0.5, 200),
        Candle("t", 0.5, 0.57, 0.45, 0.5, 220),
        Candle("t", 0.5, 0.56, 0.46, 0.5, 230),
        Candle("t", 0.5, 0.55, 0.47, 0.5, 240),
        Candle("t", 0.5, 0.54, 0.48, 0.5, 250),
        Candle("t", 0.5, 0.53, 0.49, 0.5, 260),
        Candle("t", 0.5, 0.57, 0.45, 0.5, 270),
        Candle("t", 0.5, 0.56, 0.46, 0.5, 280),
    ]
    assert narrow_sideways(candles)


def test_is_doji_true():
    c = Candle("t", 1.0, 1.1, 0.9, 1.01, 100)
    assert is_doji(c)


def test_liquidity_tower_index():
    candles = [
        Candle("t", 1, 1, 1, 1, 100),
        Candle("t", 1, 1, 1, 1, 2000),
        Candle("t", 1, 1, 1, 1, 700),
    ]
    assert liquidity_tower(candles) == 1
