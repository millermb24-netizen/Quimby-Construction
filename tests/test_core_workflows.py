from decimal import Decimal

import app as quimby


def test_estimate_math_is_user_supplied_not_invented(auth_client, app):
    response = auth_client.post('/estimates', data={
        'job_id': '1', 'labor_hours': '2.5', 'hourly_rate': '100',
        'materials': '50', 'other': '10', 'markup': '10',
        'description': 'Synthetic pricing entered for a test only.',
    })
    assert response.status_code == 302
    with app.app_context():
        estimate = quimby.db.session.scalar(quimby.db.select(quimby.Estimate))
        assert estimate.total == Decimal('341.00')


def test_job_page_lists_reports(auth_client):
    auth_client.post('/jobs/1/reports/new', data={
        'title': 'Listed Report', 'report_date': '2026-10-28',
        'services_performed': 'Work', 'findings': 'Finding',
    })
    response = auth_client.get('/jobs/1')
    assert response.status_code == 200
    assert b'Listed Report' in response.data
    assert b'Create a job report' in response.data

