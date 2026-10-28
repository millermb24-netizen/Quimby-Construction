import pytest
from werkzeug.security import generate_password_hash

import app as quimby


@pytest.fixture()
def app(tmp_path):
    quimby.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test.db'}",
        UPLOAD_FOLDER=str(tmp_path / 'uploads'),
    )
    (tmp_path / 'uploads').mkdir()
    with quimby.app.app_context():
        quimby.db.session.remove()
        quimby.db.drop_all()
        quimby.db.create_all()
        user = quimby.User(username='tester', password_hash=generate_password_hash('test-password-123'))
        customer = quimby.Customer(
            name='Sample Homeowner', email='sample@example.test',
            address='100 Sample Street', phone='555-0100')
        job = quimby.Job(customer=customer, service='Chimney inspection', notes='Synthetic test job')
        other_customer = quimby.Customer(name='Other Sample')
        other_job = quimby.Job(customer=other_customer, service='Masonry repair')
        quimby.db.session.add_all([user, customer, job, other_customer, other_job])
        quimby.db.session.flush()
        quimby.db.session.add_all([
            quimby.Photo(job_id=job.id, filename='job.jpg', original_name='job.jpg', category='Before'),
            quimby.Photo(job_id=other_job.id, filename='other.jpg', original_name='other.jpg', category='Before'),
            quimby.ReportTemplate(name='Standard report', services_intro='Starter services',
                                   findings_intro='Starter findings', recommendations_intro='Starter next steps',
                                   is_default=True),
        ])
        quimby.db.session.commit()
    yield quimby.app
    with quimby.app.app_context():
        quimby.db.session.remove()
        quimby.db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    response = client.post('/login', data={'username': 'tester', 'password': 'test-password-123'})
    assert response.status_code == 302
    return client

