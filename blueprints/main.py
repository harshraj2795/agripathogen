from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, flash, send_file, abort)
from flask_login import login_required, current_user
from io import BytesIO
from PIL import Image
from collections import Counter
from extensions import db
from models import Scan
from ml_model import predict, TREATMENTS
from pdf_report import generate_scan_report
from forms import NoteForm

main = Blueprint('main', __name__)


@main.route('/')
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


# ── Dashboard ──────────────────────────────────────────────────────────────
@main.route('/dashboard')
@login_required
def dashboard():
    scans = Scan.query.filter_by(user_id=current_user.id)\
                      .order_by(Scan.scanned_at.desc()).all()
    total = len(scans)
    last_scan = scans[0].scanned_at.strftime('%d %b %Y') if scans else None

    disease_counts = Counter(s.disease for s in scans)
    chart_labels   = list(disease_counts.keys())
    chart_data     = list(disease_counts.values())

    crop_counts = Counter(s.crop for s in scans)

    return render_template(
        'main/dashboard.html',
        scans=scans[:5],
        total=total,
        last_scan=last_scan,
        chart_labels=chart_labels,
        chart_data=chart_data,
        crop_counts=dict(crop_counts),
        most_disease=current_user.most_detected_disease(),
    )


# ── Scan (predict) ─────────────────────────────────────────────────────────
@main.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'GET':
        return render_template('main/scan.html')

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        img = Image.open(file).convert('RGB')
        disease, confidence, treatment, crop = predict(img)

        scan_obj = Scan(
            user_id    = current_user.id,
            disease    = disease,
            confidence = confidence,
            severity   = treatment.get('severity', 'medium'),
            crop       = crop,
            image_name = file.filename,
        )
        db.session.add(scan_obj)
        db.session.commit()

        return jsonify({
            'scan_id':    scan_obj.id,
            'prediction': disease,
            'confidence': confidence,
            'crop':       crop,
            'treatment':  treatment,
        })
    except Exception as e:
        print(f'Scan error: {e}')
        return jsonify({'error': 'Failed to process image.'}), 500


# ── Update note on a scan ──────────────────────────────────────────────────
@main.route('/scan/<int:scan_id>/note', methods=['POST'])
@login_required
def update_note(scan_id):
    scan_obj = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    note = request.form.get('note', '').strip()
    scan_obj.note = note[:300]
    db.session.commit()
    return jsonify({'ok': True, 'note': scan_obj.note})


# ── History ────────────────────────────────────────────────────────────────
@main.route('/history')
@login_required
def history():
    crop_filter = request.args.get('crop', '')
    query = Scan.query.filter_by(user_id=current_user.id)
    if crop_filter:
        query = query.filter_by(crop=crop_filter)
    scans = query.order_by(Scan.scanned_at.desc()).all()
    crops = ['Corn', 'Pepper', 'Potato', 'Tomato']
    return render_template('main/history.html', scans=scans,
                           crops=crops, active_crop=crop_filter)


# ── Delete scan ────────────────────────────────────────────────────────────
@main.route('/scan/<int:scan_id>/delete', methods=['POST'])
@login_required
def delete_scan(scan_id):
    scan_obj = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    db.session.delete(scan_obj)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})
    flash('Scan deleted.', 'info')
    return redirect(url_for('main.history'))


# ── Download PDF report ────────────────────────────────────────────────────
@main.route('/scan/<int:scan_id>/report')
@login_required
def download_report(scan_id):
    scan_obj = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    treatment = TREATMENTS.get(scan_obj.disease, {})
    pdf_bytes = generate_scan_report(scan_obj, treatment)
    filename  = f'agripathogen_report_{scan_obj.id}.pdf'
    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


# ── Profile ────────────────────────────────────────────────────────────────
@main.route('/profile')
@login_required
def profile():
    scans = Scan.query.filter_by(user_id=current_user.id).all()
    total = len(scans)
    disease_counts = Counter(s.disease for s in scans)
    most_common = disease_counts.most_common(3)
    crop_counts = Counter(s.crop for s in scans)
    return render_template(
        'main/profile.html',
        total=total,
        most_common=most_common,
        crop_counts=dict(crop_counts),
        member_since=current_user.created_at.strftime('%d %B %Y'),
    )