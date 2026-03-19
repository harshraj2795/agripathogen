from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from extensions import db, bcrypt, mail
from models import User
from forms import SignupForm, LoginForm, RequestResetForm, ResetPasswordForm

auth = Blueprint('auth', __name__)


def _send_confirmation_email(user):
    token = user.get_confirmation_token()
    link  = url_for('auth.confirm_email', token=token, _external=True)
    msg   = Message('Confirm your AGRI-PATHogen account', recipients=[user.email])
    msg.html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#0b120e">🌿 Confirm your account</h2>
      <p>Hi {user.name}, thanks for signing up!</p>
      <p>Click the button below to confirm your email address. The link expires in 1 hour.</p>
      <a href="{link}" style="display:inline-block;margin:16px 0;padding:12px 28px;
         background:#00cc7a;color:#0b120e;border-radius:8px;
         text-decoration:none;font-weight:700">Confirm Email</a>
      <p style="color:#718096;font-size:13px">If you didn't sign up, ignore this email.</p>
    </div>"""
    mail.send(msg)


def _send_reset_email(user):
    token = user.get_reset_token()
    link  = url_for('auth.reset_password', token=token, _external=True)
    msg   = Message('Reset your AGRI-PATHogen password', recipients=[user.email])
    msg.html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#0b120e">🔑 Password Reset</h2>
      <p>Hi {user.name},</p>
      <p>Click below to reset your password. The link expires in 30 minutes.</p>
      <a href="{link}" style="display:inline-block;margin:16px 0;padding:12px 28px;
         background:#00cc7a;color:#0b120e;border-radius:8px;
         text-decoration:none;font-weight:700">Reset Password</a>
      <p style="color:#718096;font-size:13px">If you didn't request this, ignore this email.</p>
    </div>"""
    mail.send(msg)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = SignupForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash('An account with that email already exists.', 'danger')
            return render_template('auth/signup.html', form=form)
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data.lower(), password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()
        try:
            _send_confirmation_email(user)
            flash('Account created! Check your email to confirm your account.', 'success')
        except Exception as e:
            print(f'Email error: {e}')
            flash('Account created but confirmation email failed. Contact support.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_confirmed:
                flash('Please confirm your email before logging in.', 'warning')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/confirm/<token>')
def confirm_email(token):
    user = User.verify_confirmation_token(token)
    if not user:
        flash('Confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
    if user.is_confirmed:
        flash('Account already confirmed.', 'info')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('Email confirmed! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/resend-confirmation')
@login_required
def resend_confirmation():
    if current_user.is_confirmed:
        return redirect(url_for('main.dashboard'))
    try:
        _send_confirmation_email(current_user)
        flash('Confirmation email resent.', 'info')
    except Exception:
        flash('Failed to send email. Try again later.', 'danger')
    return redirect(url_for('auth.login'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            try:
                _send_reset_email(user)
            except Exception as e:
                print(f'Reset email error: {e}')
        flash('If that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('Reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.commit()
        flash('Password updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)