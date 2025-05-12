from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from datetime import datetime, timedelta
import random

login_attempts = {}

main = Blueprint('main', __name__)

current_rpm = 0

thresholds = {
    "rpm": 3000,
    "temperature": 80,
    "pressure": 5
}
# 사용자 계정 정보(하드 코딩 해놓고 추후에 확인)
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "guest": {"password": "guest123", "role": "guest"},
}
@main.route('/status')
def status():
    import random
    return jsonify({
        "rpm": current_rpm,
        "temperature": random.randint(20, 100),
        "pressure": round(random.uniform(1.0, 10.0), 2),
        "thresholds": thresholds  # 실시간 경고 임계값 전달
    })

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        now = datetime.now()
        user_record = login_attempts.get(username, {"count": 0, "locked_until": None})

        # 🔒 잠금 시간 확인
        if user_record["locked_until"] and now < user_record["locked_until"]:
            wait_time = int((user_record["locked_until"] - now).total_seconds() // 60) + 1
            return render_template('login.html', error=f"❌ Your account has been locked. Please try again in {wait_time}minutes.")

        # 🔓 로그인 성공
        if user and user["password"] == password:
            session['username'] = username
            session['role'] = user['role']
            login_attempts[username] = {"count": 0, "locked_until": None}
            return redirect(url_for('main.index'))

        # ❌ 로그인 실패
        user_record["count"] += 1
        if user_record["count"] >= 5:
            user_record["locked_until"] = now + timedelta(minutes=5)
            error = "❌ Your account has been locked for 5 minutes due to 5 failed login attempts."
        else:
            remaining = 5 - user_record["count"]
            error = f"Login failed. Number of attempts remaining: {remaining}"

        login_attempts[username] = user_record
        return render_template('login.html', error=error)

    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/admin/reset_user', methods=['POST'])
def reset_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "Error, You don't have permission.", 403

    username = request.form.get('target_user')
    if username in login_attempts:
        login_attempts[username] = {"count": 0, "locked_until": None}
        return f"{username}'s Login attempts have been reset."
    else:
        return f"{username} << No login history'."

@main.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    return render_template(
        'index.html',
        rpm=current_rpm,
        username=session['username'],
        role=session['role'],
        thresholds=thresholds
    )

@main.route('/set_rpm', methods=['POST'])
def set_rpm():
    global current_rpm
    if 'username' not in session:
        return redirect(url_for('main.login'))
    # admin만 제어 허용
    if session.get('role') != 'admin':
        return render_template('index.html', rpm=current_rpm, username=session['username'], role=session['role'],
                               error="⚠️ 권한이 없습니다.")


    new_rpm = int(request.form['rpm'])
    current_rpm = new_rpm
    return render_template('index.html', rpm=current_rpm, username=session['username'], role=session['role'])