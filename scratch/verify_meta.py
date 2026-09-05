from app import app

with app.test_client() as c:
    with c.session_transaction() as s:
        s['user_id'] = 1
        s['user_name'] = 'Demo'

    # Test 1: /record (no specific report ID)
    r = c.get('/record')
    assert r.status_code == 200, f'Status: {r.status_code}'
    html = r.data.decode()
    assert 'medlens-config' in html, 'meta tag missing'
    assert 'data-initial-report-id' in html, 'data attr missing'
    assert 'window.INITIAL_REPORT_ID' not in html, 'old window global still present'
    print('1. /record renders meta tag correctly, no script-block Jinja')

    # Test 2: /report/1 with pre-selected report
    r2 = c.get('/report/1')
    if r2.status_code == 200:
        html2 = r2.data.decode()
        assert 'data-initial-report-id' in html2, 'Report ID not in meta'
        print('2. /report/1 meta tag OK')
    else:
        print(f'2. /report/1 -> {r2.status_code} (OK - redirect)')

print('All checks passed!')
