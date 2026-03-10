from dashboard import build_dashboard_data, render_dashboard_html


def test_dashboard_data_has_signals():
    data = build_dashboard_data("sample_data.json", "1h")
    assert data["contracts_total"] >= 1
    assert "signals" in data


def test_dashboard_html_contains_table():
    data = build_dashboard_data("sample_data.json", "1h")
    html = render_dashboard_html(data)
    assert "الصفقات المقترحة" in html
    assert "<table>" in html
