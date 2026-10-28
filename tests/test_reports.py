import app as quimby


def test_reports_require_login(client):
    response = client.get('/jobs/1/reports/new')
    assert response.status_code == 302
    assert '/login' in response.location


def test_create_preview_finalize_reopen_report(auth_client, app):
    response = auth_client.post('/jobs/1/reports/new', data={
        'title': 'Inspection Report',
        'report_date': '2026-10-28',
        'services_performed': 'Inspected the chimney exterior.',
        'findings': 'Observed minor mortar wear.',
        'recommendations': 'Monitor annually.',
        'template_id': '1',
        'photo_ids': ['1'],
        'caption_1': 'Synthetic before photo',
    })
    assert response.status_code == 302
    assert response.location.endswith('/reports/1/edit')

    with app.app_context():
        report = quimby.db.session.get(quimby.JobReport, 1)
        assert report.status == 'Draft'
        assert report.template.name == 'Standard report'
        assert [(item.photo_id, item.caption) for item in report.report_photos] == [(1, 'Synthetic before photo')]

    preview = auth_client.get('/reports/1/preview')
    assert preview.status_code == 200
    assert b'Inspection Report' in preview.data
    assert b'Observed minor mortar wear.' in preview.data

    final = auth_client.post('/reports/1/finalize')
    assert final.status_code == 302
    locked = auth_client.post('/reports/1/edit', data={
        'title': 'Changed', 'report_date': '2026-10-28',
        'services_performed': 'Changed', 'findings': 'Changed'})
    assert locked.status_code == 409

    reopened = auth_client.post('/reports/1/reopen')
    assert reopened.status_code == 302
    with app.app_context():
        assert quimby.db.session.get(quimby.JobReport, 1).status == 'Draft'


def test_report_rejects_photos_from_another_job(auth_client, app):
    auth_client.post('/jobs/1/reports/new', data={
        'title': 'Safe Report', 'report_date': '2026-10-28',
        'services_performed': 'Completed inspection.', 'findings': 'No concern.',
        'photo_ids': ['2'], 'caption_2': 'Should not be attached',
    })
    with app.app_context():
        report = quimby.db.session.get(quimby.JobReport, 1)
        assert report.report_photos == []


def test_pdf_download_and_delivery_preview(auth_client, app):
    auth_client.post('/jobs/1/reports/new', data={
        'title': 'PDF Report', 'report_date': '2026-10-28',
        'services_performed': 'Completed synthetic service.',
        'findings': 'Synthetic finding.', 'recommendations': 'Synthetic recommendation.',
    })
    pdf = auth_client.get('/reports/1/pdf')
    assert pdf.status_code == 200
    assert pdf.mimetype == 'application/pdf'
    assert pdf.data.startswith(b'%PDF')
    assert 'quimby-job-1-report-1.pdf' in pdf.headers['Content-Disposition']

    delivery = auth_client.post('/reports/1/delivery-preview', data={
        'recipient': 'preview@example.test', 'note': 'Preview only'})
    assert delivery.status_code == 302
    with app.app_context():
        saved = quimby.db.session.scalar(quimby.db.select(quimby.ReportDelivery))
        assert saved.status == 'Draft preview'
        assert saved.recipient == 'preview@example.test'
        assert quimby.db.session.scalar(
            quimby.db.select(quimby.Audit).filter_by(action='Report delivery preview saved')) is not None


def test_new_report_uses_default_template(auth_client):
    response = auth_client.get('/jobs/1/reports/new')
    assert response.status_code == 200
    assert b'Starter services' in response.data
    assert b'Starter findings' in response.data
    assert b'<option value="1" selected>' in response.data


def test_templates_can_be_created_and_edited(auth_client, app):
    created = auth_client.post('/report-templates', data={
        'name': 'Repair follow-up', 'services_intro': 'Initial wording',
        'findings_intro': 'Initial findings', 'recommendations_intro': 'Initial recommendation',
    })
    assert created.status_code == 302
    updated = auth_client.post('/report-templates/2/edit', data={
        'name': 'Repair closeout', 'services_intro': 'Updated wording',
        'findings_intro': 'Updated findings', 'recommendations_intro': 'Updated recommendation',
        'is_default': 'on',
    })
    assert updated.status_code == 302
    with app.app_context():
        edited = quimby.db.session.get(quimby.ReportTemplate, 2)
        original = quimby.db.session.get(quimby.ReportTemplate, 1)
        assert edited.name == 'Repair closeout'
        assert edited.is_default is True
        assert original.is_default is False

