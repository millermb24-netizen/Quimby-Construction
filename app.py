import os, json, uuid
from io import BytesIO
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from decimal import Decimal

app=Flask(__name__)
app.config['SECRET_KEY']=os.environ.get('SECRET_KEY','development-only-change-me')
app.config['SQLALCHEMY_DATABASE_URI']=os.environ.get('DATABASE_URL','sqlite:///quimby.db').replace('postgres://','postgresql+psycopg://',1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['MAX_CONTENT_LENGTH']=12*1024*1024
app.config['UPLOAD_FOLDER']=os.environ.get('UPLOAD_FOLDER',os.path.join(app.instance_path,'uploads'))
if os.environ.get('APP_ENV')=='production' and app.config['SECRET_KEY']=='development-only-change-me':
    raise RuntimeError('Set SECRET_KEY in production')
if os.environ.get('APP_ENV') in ('staging','production') and app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
    raise RuntimeError('Configure persistent PostgreSQL DATABASE_URL for hosted environments')
app.config['SESSION_COOKIE_HTTPONLY']=True
app.config['SESSION_COOKIE_SAMESITE']='Lax'
app.config['SESSION_COOKIE_SECURE']=os.environ.get('APP_ENV') in ('staging','production')
os.makedirs(app.instance_path,exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'],exist_ok=True)
db=SQLAlchemy(app)
csrf=CSRFProtect(app)
login_manager=LoginManager(app)
login_manager.login_view='login'
migrate=Migrate(app,db)

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)
class Customer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(180),nullable=False)
    phone=db.Column(db.String(60),default='')
    email=db.Column(db.String(180),default='')
    address=db.Column(db.String(300),default='')
    notes=db.Column(db.Text,default='')
class Job(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    customer_id=db.Column(db.Integer,db.ForeignKey('customer.id'),nullable=False)
    customer=db.relationship('Customer',backref='jobs')
    service=db.Column(db.String(120),nullable=False)
    status=db.Column(db.String(30),default='Inquiry')
    preferred_date=db.Column(db.String(40),default='')
    appointment_date=db.Column(db.String(40),default='')
    arrival_window=db.Column(db.String(80),default='')
    notes=db.Column(db.Text,default='')
    checklist=db.Column(db.Text,default='{}')
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Estimate(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    job_id=db.Column(db.Integer,db.ForeignKey('job.id'),nullable=False)
    job=db.relationship('Job',backref='estimates')
    labor_hours=db.Column(db.Numeric(12,2),default=0)
    hourly_rate=db.Column(db.Numeric(12,2),default=0)
    materials=db.Column(db.Numeric(12,2),default=0)
    other=db.Column(db.Numeric(12,2),default=0)
    markup=db.Column(db.Numeric(12,2),default=0)
    total=db.Column(db.Numeric(12,2),default=0)
    description=db.Column(db.Text,default='')
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Photo(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    job_id=db.Column(db.Integer,db.ForeignKey('job.id'),nullable=False)
    filename=db.Column(db.String(200),nullable=False)
    original_name=db.Column(db.String(200),nullable=False)
    category=db.Column(db.String(30),default='Before')
class Audit(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),nullable=False)
    action=db.Column(db.String(100),nullable=False)
    details=db.Column(db.Text,default='')
    timestamp=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class ReportTemplate(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),unique=True,nullable=False)
    services_intro=db.Column(db.Text,default='')
    findings_intro=db.Column(db.Text,default='')
    recommendations_intro=db.Column(db.Text,default='')
    is_default=db.Column(db.Boolean,default=False,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
class JobReport(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    job_id=db.Column(db.Integer,db.ForeignKey('job.id'),nullable=False,index=True)
    template_id=db.Column(db.Integer,db.ForeignKey('report_template.id'))
    job=db.relationship('Job',backref=db.backref('reports',lazy=True,order_by='JobReport.created_at.desc()'))
    template=db.relationship('ReportTemplate')
    title=db.Column(db.String(180),nullable=False,default='Job Report')
    report_date=db.Column(db.String(10),nullable=False)
    services_performed=db.Column(db.Text,default='',nullable=False)
    findings=db.Column(db.Text,default='',nullable=False)
    recommendations=db.Column(db.Text,default='',nullable=False)
    status=db.Column(db.String(20),default='Draft',nullable=False)
    finalized_at=db.Column(db.DateTime(timezone=True))
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    updated_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)
class ReportPhoto(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    report_id=db.Column(db.Integer,db.ForeignKey('job_report.id',ondelete='CASCADE'),nullable=False,index=True)
    photo_id=db.Column(db.Integer,db.ForeignKey('photo.id'),nullable=False)
    caption=db.Column(db.String(300),default='')
    sort_order=db.Column(db.Integer,default=0,nullable=False)
    report=db.relationship('JobReport',backref=db.backref('report_photos',lazy=True,cascade='all, delete-orphan',order_by='ReportPhoto.sort_order'))
    photo=db.relationship('Photo')
    __table_args__=(db.UniqueConstraint('report_id','photo_id',name='uq_report_photo'),)
class ReportDelivery(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    report_id=db.Column(db.Integer,db.ForeignKey('job_report.id',ondelete='CASCADE'),nullable=False,index=True)
    recipient=db.Column(db.String(180),nullable=False)
    status=db.Column(db.String(30),default='Draft preview',nullable=False)
    note=db.Column(db.String(500),default='')
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    report=db.relationship('JobReport',backref=db.backref('deliveries',lazy=True,cascade='all, delete-orphan',order_by='ReportDelivery.created_at.desc()'))

@login_manager.user_loader
def load_user(uid): return db.session.get(User,int(uid))
def audit(action,details=''):
    db.session.add(Audit(username=current_user.username,action=action,details=details))
def val(name):
    try: return max(Decimal('0'),Decimal(request.form.get(name,'0') or '0'))
    except Exception: return Decimal('0')
def clean_text(name,limit):return request.form.get(name,'').strip()[:limit]
def report_form_data(report):
    report.title=clean_text('title',180) or 'Job Report'
    report.report_date=clean_text('report_date',10) or datetime.now().strftime('%Y-%m-%d')
    report.services_performed=clean_text('services_performed',12000)
    report.findings=clean_text('findings',12000)
    report.recommendations=clean_text('recommendations',12000)
    template_id=request.form.get('template_id',type=int)
    report.template=db.session.get(ReportTemplate,template_id) if template_id else None
def sync_report_photos(report):
    selected={int(value) for value in request.form.getlist('photo_ids') if value.isdigit()}
    allowed={p.id for p in db.session.scalars(db.select(Photo).filter_by(job_id=report.job_id)).all()}
    selected &= allowed
    existing={rp.photo_id:rp for rp in report.report_photos}
    for photo_id,rp in list(existing.items()):
        if photo_id not in selected:db.session.delete(rp)
    for order,photo_id in enumerate(sorted(selected)):
        rp=existing.get(photo_id) or ReportPhoto(report=report,photo_id=photo_id)
        rp.sort_order=order
        rp.caption=clean_text(f'caption_{photo_id}',300)
        db.session.add(rp)
def template_form_data(template):
    template.name=clean_text('name',120)
    template.services_intro=clean_text('services_intro',12000)
    template.findings_intro=clean_text('findings_intro',12000)
    template.recommendations_intro=clean_text('recommendations_intro',12000)
    template.is_default='is_default' in request.form
    if template.is_default:
        db.session.execute(db.update(ReportTemplate).where(ReportTemplate.id != template.id).values(is_default=False))
def template_payload(templates):
    return {str(t.id):{'services':t.services_intro or '','findings':t.findings_intro or '','recommendations':t.recommendations_intro or ''} for t in templates}

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=db.session.scalar(db.select(User).filter_by(username=request.form.get('username','')))
        if u and check_password_hash(u.password_hash,request.form.get('password','')):
            login_user(u);return redirect(url_for('index'))
        flash('Incorrect username or password.')
    return render_template('login.html')
@app.post('/logout')
@login_required
def logout(): logout_user();return redirect(url_for('login'))
@app.get('/')
@login_required
def index():
    jobs=db.session.scalars(db.select(Job).order_by(Job.id.desc())).all()
    return render_template('index.html',jobs=jobs,customers=db.session.scalars(db.select(Customer).order_by(Customer.name)).all(),estimates=db.session.scalars(db.select(Estimate).order_by(Estimate.id.desc()).limit(20)).all(),audits=db.session.scalars(db.select(Audit).order_by(Audit.id.desc()).limit(15)).all(),today=datetime.now().strftime('%Y-%m-%d'))
@app.post('/customers')
@login_required
def add_customer():
    name=request.form.get('name','').strip()
    if not name:abort(400)
    c=Customer(name=name,phone=request.form.get('phone','').strip(),email=request.form.get('email','').strip(),address=request.form.get('address','').strip())
    db.session.add(c);db.session.flush();audit('Customer created',f'Customer #{c.id}');db.session.commit();return redirect(url_for('index')+'#customers')
@app.post('/jobs')
@login_required
def add_job():
    customer=db.session.get(Customer,request.form.get('customer_id',type=int))
    if not customer:abort(400)
    j=Job(customer_id=customer.id,service=request.form.get('service','Inspection')[:120],preferred_date=request.form.get('preferred_date','')[:40],notes=request.form.get('notes','')[:5000])
    db.session.add(j);db.session.flush();audit('Inquiry created',f'Job #{j.id}');db.session.commit();return redirect(url_for('index')+'#jobs')
@app.post('/jobs/<int:job_id>/schedule')
@login_required
def schedule(job_id):
    j=db.get_or_404(Job,job_id)
    date=request.form.get('appointment_date','')[:40]
    if not date:abort(400)
    j.appointment_date=date;j.arrival_window=request.form.get('arrival_window','')[:80];j.status='Scheduled'
    audit('Appointment scheduled',f'Job #{j.id}: {date}');db.session.commit();flash('Saved locally. No Google Calendar event or SMS was sent.');return redirect(url_for('index')+'#jobs')
@app.post('/jobs/<int:job_id>/status')
@login_required
def status(job_id):
    j=db.get_or_404(Job,job_id);status=request.form.get('status')
    if status not in ('Inquiry','Scheduled','In Progress','Completed','Cancelled'):abort(400)
    j.status=status;audit('Job status changed',f'Job #{j.id}: {status}');db.session.commit();return redirect(url_for('index')+'#jobs')
@app.post('/jobs/<int:job_id>/checklist')
@login_required
def checklist(job_id):
    j=db.get_or_404(Job,job_id)
    keys=('crown','mortar','flashing','brick','access')
    j.checklist=json.dumps({k:k in request.form for k in keys});audit('Checklist updated',f'Job #{j.id}');db.session.commit();return redirect(url_for('index')+'#jobs')
@app.post('/estimates')
@login_required
def add_estimate():
    j=db.get_or_404(Job,request.form.get('job_id',type=int))
    hours,rate,materials,other,markup=[val(k) for k in ('labor_hours','hourly_rate','materials','other','markup')]
    total=((hours*rate+materials+other)*(1+markup/100)).quantize(Decimal('.01'))
    e=Estimate(job_id=j.id,labor_hours=hours,hourly_rate=rate,materials=materials,other=other,markup=markup,total=total,description=request.form.get('description','')[:10000])
    db.session.add(e);db.session.flush();audit('Estimate created',f'Estimate #{e.id}, job #{j.id}, ${total}');db.session.commit();return redirect(url_for('index')+'#estimates')
@app.post('/jobs/<int:job_id>/photos')
@login_required
def upload_photo(job_id):
    db.get_or_404(Job,job_id);f=request.files.get('photo')
    if not f or not f.filename:abort(400)
    data=f.read()
    if len(data)>10*1024*1024:abort(413)
    if data.startswith(b'\xff\xd8\xff'): extension='jpg'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'): extension='png'
    elif data.startswith(b'RIFF') and data[8:12]==b'WEBP': extension='webp'
    else: abort(400,'Only JPEG, PNG and WebP photos are allowed')
    filename=f'{uuid.uuid4().hex}.{extension}'
    with open(os.path.join(app.config['UPLOAD_FOLDER'],filename),'wb') as output:output.write(data)
    db.session.add(Photo(job_id=job_id,filename=filename,original_name=secure_filename(f.filename)[:200],category=request.form.get('category','Before')[:30]))
    audit('Photo uploaded',f'Job #{job_id}');db.session.commit();return redirect(url_for('job_detail',job_id=job_id))
@app.get('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):return render_template('job.html',job=db.get_or_404(Job,job_id),photos=db.session.scalars(db.select(Photo).filter_by(job_id=job_id)).all())
@app.route('/jobs/<int:job_id>/reports/new',methods=['GET','POST'])
@login_required
def new_report(job_id):
    job=db.get_or_404(Job,job_id)
    templates=db.session.scalars(db.select(ReportTemplate).order_by(ReportTemplate.is_default.desc(),ReportTemplate.name)).all()
    if request.method=='POST':
        report=JobReport(job=job,report_date=datetime.now().strftime('%Y-%m-%d'))
        report_form_data(report);db.session.add(report);db.session.flush();sync_report_photos(report)
        audit('Job report created',f'Report #{report.id}, job #{job.id}');db.session.commit();flash('Draft report created.')
        return redirect(url_for('edit_report',report_id=report.id))
    default=next((t for t in templates if t.is_default),templates[0] if templates else None)
    report=JobReport(job_id=job.id,title=f'{job.service} Report',report_date=datetime.now().strftime('%Y-%m-%d'),services_performed=default.services_intro if default else '',findings=default.findings_intro if default else '',recommendations=default.recommendations_intro if default else '',template=default)
    photos=db.session.scalars(db.select(Photo).filter_by(job_id=job.id).order_by(Photo.id)).all()
    return render_template('report_form.html',report=report,job=job,photos=photos,templates=templates,template_data=template_payload(templates),is_new=True)
@app.route('/reports/<int:report_id>/edit',methods=['GET','POST'])
@login_required
def edit_report(report_id):
    report=db.get_or_404(JobReport,report_id)
    if request.method=='POST':
        if report.status=='Final':abort(409,'Reopen the report before editing it.')
        report_form_data(report);sync_report_photos(report);audit('Job report updated',f'Report #{report.id}');db.session.commit();flash('Draft report saved.')
        return redirect(url_for('edit_report',report_id=report.id))
    photos=db.session.scalars(db.select(Photo).filter_by(job_id=report.job_id).order_by(Photo.id)).all()
    templates=db.session.scalars(db.select(ReportTemplate).order_by(ReportTemplate.is_default.desc(),ReportTemplate.name)).all()
    return render_template('report_form.html',report=report,job=report.job,photos=photos,templates=templates,template_data=template_payload(templates),is_new=False)
@app.get('/reports/<int:report_id>/preview')
@login_required
def preview_report(report_id):return render_template('report_preview.html',report=db.get_or_404(JobReport,report_id))
@app.post('/reports/<int:report_id>/finalize')
@login_required
def finalize_report(report_id):
    report=db.get_or_404(JobReport,report_id)
    if not report.services_performed or not report.findings:abort(400,'Services performed and findings are required before finalizing.')
    report.status='Final';report.finalized_at=datetime.now(timezone.utc);audit('Job report finalized',f'Report #{report.id}');db.session.commit();flash('Report finalized and locked.')
    return redirect(url_for('preview_report',report_id=report.id))
@app.post('/reports/<int:report_id>/reopen')
@login_required
def reopen_report(report_id):
    report=db.get_or_404(JobReport,report_id);report.status='Draft';report.finalized_at=None;audit('Job report reopened',f'Report #{report.id}');db.session.commit();flash('Report reopened for editing.')
    return redirect(url_for('edit_report',report_id=report.id))
@app.get('/reports/<int:report_id>/pdf')
@login_required
def report_pdf(report_id):
    from report_pdf import build_report_pdf
    report=db.get_or_404(JobReport,report_id)
    pdf=build_report_pdf(report,app.config['UPLOAD_FOLDER'])
    return send_file(BytesIO(pdf),mimetype='application/pdf',as_attachment=True,download_name=f'quimby-job-{report.job_id}-report-{report.id}.pdf')
@app.post('/reports/<int:report_id>/delivery-preview')
@login_required
def delivery_preview(report_id):
    report=db.get_or_404(JobReport,report_id);recipient=clean_text('recipient',180)
    if not recipient or '@' not in recipient:abort(400,'Enter a valid recipient email.')
    delivery=ReportDelivery(report=report,recipient=recipient,status='Draft preview',note=clean_text('note',500))
    db.session.add(delivery);audit('Report delivery preview saved',f'Report #{report.id} for {recipient}');db.session.commit();flash('Delivery preview saved. No email was sent.')
    return redirect(url_for('preview_report',report_id=report.id))
@app.route('/report-templates',methods=['GET','POST'])
@login_required
def report_templates():
    if request.method=='POST':
        name=clean_text('name',120)
        if not name:abort(400)
        if db.session.scalar(db.select(ReportTemplate.id).filter_by(name=name)):abort(409,'A report template with that name already exists.')
        template=ReportTemplate(name=name);db.session.add(template);db.session.flush();template_form_data(template)
        db.session.add(template);audit('Report template created',name);db.session.commit();flash('Report template saved.')
        return redirect(url_for('report_templates'))
    return render_template('report_templates.html',templates=db.session.scalars(db.select(ReportTemplate).order_by(ReportTemplate.name)).all())
@app.route('/report-templates/<int:template_id>/edit',methods=['GET','POST'])
@login_required
def edit_report_template(template_id):
    template=db.get_or_404(ReportTemplate,template_id)
    if request.method=='POST':
        name=clean_text('name',120)
        duplicate=db.session.scalar(db.select(ReportTemplate.id).where(ReportTemplate.name==name,ReportTemplate.id!=template.id))
        if not name:abort(400)
        if duplicate:abort(409,'A report template with that name already exists.')
        template_form_data(template);audit('Report template updated',f'Template #{template.id}');db.session.commit();flash('Report template updated.')
        return redirect(url_for('report_templates'))
    return render_template('report_template_edit.html',template=template)
@app.get('/photos/<int:photo_id>')
@login_required
def photo_file(photo_id):
    p=db.get_or_404(Photo,photo_id);return send_from_directory(app.config['UPLOAD_FOLDER'],p.filename)
@app.cli.command('init-db')
def init_db():
    with app.app_context():db.create_all();print('Tables created. Use migrations before production schema changes.')
@app.cli.command('seed-report-templates')
def seed_report_templates():
    with app.app_context():
        if db.session.scalar(db.select(ReportTemplate.id).limit(1)) is None:
            db.session.add(ReportTemplate(name='Standard chimney service report',services_intro='Work was completed in accordance with the agreed scope.',findings_intro='The following conditions were observed during the service and inspection:',recommendations_intro='Based on the conditions observed, Quimby Construction recommends:',is_default=True));db.session.commit();print('Default report template created.')
        else:print('Report templates already exist; no changes made.')
@app.cli.command('create-admin')
def create_admin():
    import getpass
    username=input('Username: ').strip()
    password=getpass.getpass('Password (12+ characters): ')
    if len(password)<12:raise RuntimeError('Password must be at least 12 characters')
    with app.app_context():
        if db.session.scalar(db.select(User).filter_by(username=username)):raise RuntimeError('User exists')
        db.session.add(User(username=username,password_hash=generate_password_hash(password)));db.session.commit();print('Admin created')

@app.cli.command('bootstrap-admin')
def bootstrap_admin():
    """Create the first account from temporary deployment secrets, once only."""
    with app.app_context():
        if db.session.scalar(db.select(User.id).limit(1)) is not None:
            print('An account already exists; bootstrap skipped.')
            return
        username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME', '').strip()
        password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD', '')
        if not username and not password:
            print('No account exists. Set BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD to create the first account.')
            return
        if not username or len(username) > 80 or len(password) < 12:
            raise RuntimeError('Bootstrap requires a username of 1-80 characters and a password of at least 12 characters')
        db.session.add(User(username=username, password_hash=generate_password_hash(password)))
        db.session.commit()
        print('First admin account created. Remove the BOOTSTRAP_ADMIN_* environment variables.')

if __name__=='__main__':app.run(debug=os.environ.get('APP_ENV','development')=='development')
