import streamlit as st
import pandas as pd
import time
from datetime import datetime
from generator import generate_question_paper
from pdf_utils import create_pdf

# ------------------------------------------------------------------------------
# PAGE CONFIG & STATE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="EduThink AI – Question Paper Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def _init_state():
    defaults = {
        'authenticated': False,
        'role': None,
        'current_user': None,
        'current_page': "login",
        'generated_paper': None,
        'paper_history': [],
        'teachers': [
            {"name": "Demo Teacher", "username": "teacher", "password": "123", "status": "Active"}
        ],
        'subjects': [
            {"name": "Data Structures", "stream": "Computer Science", "description": "Core CS Subject"},
            {"name": "Algorithms", "stream": "Computer Science", "description": "Advanced CS"},
            {"name": "Database Management", "stream": "Computer Science", "description": "SQL & NoSQL"},
            {"name": "Operating Systems", "stream": "Computer Science", "description": "Process & Memory Management"},
            {"name": "Mechanics", "stream": "Engineering", "description": "Core Engineering"},
            {"name": "Thermodynamics", "stream": "Engineering", "description": "Heat & Energy"},
            {"name": "Financial Accounting", "stream": "Accounting", "description": "Basic Acc"},
            {"name": "Science", "stream": "School", "description": "General Science"}
        ],
        'settings': {
            "allow_teacher_add_subject": False,
            "institution_name": "Dr. D.Y. Patil College of Engineering and Technology",
            "require_approval": True
        },
        'notifications': {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

def add_notification(username, msg, msg_type="info"):
    if username not in st.session_state.notifications:
        st.session_state.notifications[username] = []
    st.session_state.notifications[username].append({
        "msg": msg, "type": msg_type,
        "time": datetime.now().strftime("%d %b, %H:%M")
    })

def go_to(page):
    st.session_state.current_page = page
    st.rerun()

# ------------------------------------------------------------------------------
# STYLING
# ------------------------------------------------------------------------------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

    :root {
        --primary: #1E3A8A;
        --primary-light: #3B82F6;
        --accent: #F59E0B;
        --bg: #F0F4FF;
        --surface: #FFFFFF;
        --text: #1F2937;
        --text-muted: #6B7280;
        --border: #E5E7EB;
        --success: #059669;
        --danger: #DC2626;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp { background: var(--bg); }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: var(--primary) !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.1rem !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: 0.01em !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(30,58,138,0.18) !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: var(--primary-light) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(59,130,246,0.3) !important;
    }
    .stButton > button:disabled {
        background: #CBD5E1 !important;
        color: #94A3B8 !important;
        cursor: not-allowed !important;
    }

    /* Cards */
    .card {
        background: var(--surface);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid var(--border);
        margin-bottom: 16px;
        transition: box-shadow 0.2s;
    }
    .card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.1); }

    .stat-card {
        background: var(--surface);
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid var(--primary);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 20px;
    }
    .stat-value { font-size: 2.2rem; font-weight: 700; color: var(--primary); font-family: 'Playfair Display', serif; }
    .stat-label { font-size: 0.9rem; color: var(--text-muted); margin-top: 4px; }

    .feature-card {
        background: var(--surface);
        border-radius: 12px;
        padding: 28px 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-top: 4px solid var(--primary);
        margin-bottom: 16px;
        min-height: 140px;
        transition: all 0.25s;
    }
    .feature-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(30,58,138,0.12); }
    .feature-card h3 { font-size: 1.15rem; margin-bottom: 8px; }
    .feature-card p { color: var(--text-muted); font-size: 0.9rem; }

    /* Paper Preview */
    .paper-wrapper {
        background: white;
        padding: 40px 48px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        border: 1px solid var(--border);
        font-family: 'DM Sans', sans-serif;
    }
    .paper-header-block {
        border-bottom: 2px solid var(--primary);
        padding-bottom: 16px;
        margin-bottom: 20px;
        text-align: center;
    }
    .paper-inst { font-size: 1.3rem; font-weight: 700; color: var(--primary); font-family: 'Playfair Display', serif; }
    .paper-sub { font-size: 1.05rem; font-weight: 600; margin-top: 6px; }
    .paper-meta { display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.9rem; color: var(--text-muted); }

    .section-header {
        background: var(--primary);
        color: white !important;
        padding: 8px 14px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.05em;
        margin: 20px 0 6px 0;
        display: inline-block;
    }
    .question-row { padding: 6px 0; border-bottom: 1px solid #F3F4F6; font-size: 0.95rem; }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-draft { background: #F3F4F6; color: #6B7280; }
    .badge-pending { background: #FEF3C7; color: #92400E; }
    .badge-approved { background: #D1FAE5; color: #065F46; }
    .badge-rejected { background: #FEE2E2; color: #991B1B; }

    /* Login */
    .login-box {
        background: white;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(30,58,138,0.12);
        border: 1px solid var(--border);
    }

    /* Sidebar-like nav */
    .nav-back {
        color: var(--primary);
        font-size: 0.9rem;
        cursor: pointer;
        font-weight: 500;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------------------------
def login_page():
    st.markdown('<div style="margin-top: 8vh;"></div>', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div class="login-box">
            <div style="text-align:center; margin-bottom:28px;">
                <div style="font-size:3rem;">🎓</div>
                <div style="font-family:'Playfair Display',serif; font-size:1.9rem; color:#1E3A8A; font-weight:700;">EduThink AI</div>
                <div style="color:#6B7280; font-size:0.95rem; margin-top:6px;">Question Paper Generator Portal</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In →")

            if submitted:
                if username == "admin" and password == "admin":
                    st.session_state.update({
                        'authenticated': True, 'role': "admin",
                        'current_user': "admin", 'current_page': "admin_dashboard"
                    })
                    st.rerun()
                else:
                    teacher = next((t for t in st.session_state.teachers
                                    if t['username'] == username and t['password'] == password), None)
                    if teacher:
                        if teacher['status'] != "Active":
                            st.error("⚠️ Your account is deactivated. Contact admin.")
                        else:
                            st.session_state.update({
                                'authenticated': True, 'role': "teacher",
                                'current_user': username, 'current_page': "dashboard"
                            })
                            st.rerun()
                    else:
                        st.error("Invalid username or password.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Demo: admin/admin or teacher/123")


def logout_button():
    if st.button("🚪 Logout", key="btn_logout"):
        for k in ['authenticated', 'role', 'current_user', 'generated_paper']:
            st.session_state[k] = False if k == 'authenticated' else None
        st.session_state.current_page = "login"
        st.rerun()


# ------------------------------------------------------------------------------
# ADMIN
# ------------------------------------------------------------------------------
def admin_dashboard_page():
    st.title("Admin Dashboard")

    pending = [p for p in st.session_state.paper_history if p.get('status') == 'Pending']
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        (len(st.session_state.teachers), "Teachers"),
        (len(st.session_state.subjects), "Subjects"),
        (len(st.session_state.paper_history), "Papers Generated"),
        (len(pending), "Pending Approvals"),
    ]
    for col, (val, label) in zip([c1, c2, c3, c4], stats):
        accent = "#DC2626" if label == "Pending Approvals" and val > 0 else "#1E3A8A"
        col.markdown(f"""
        <div class="stat-card" style="border-left-color:{accent};">
            <div class="stat-value" style="color:{accent};">{val}</div>
            <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    pages = [
        ("col1", "👥 Manage Teachers", "Add, edit, activate/deactivate teachers", "admin_manage_teachers"),
        ("col2", "📚 Manage Subjects", "Configure subjects and stream assignments", "admin_manage_subjects"),
        ("col3", "📝 Review Papers", "Approve or reject teacher submissions", "admin_view_papers"),
    ]
    for (colname, title, desc, page), col in zip(pages, [col1, col2, col3]):
        with col:
            st.markdown(f"<div class='feature-card'><h3>{title}</h3><p>{desc}</p></div>", unsafe_allow_html=True)
            if st.button(title.split(" ", 1)[1], key=f"admin_{page}"):
                go_to(page)

    st.markdown("---")
    logout_button()


def admin_manage_teachers_page():
    if st.button("← Admin Dashboard"): go_to("admin_dashboard")
    st.title("Manage Teachers")

    with st.expander("➕ Add New Teacher"):
        with st.form("add_teacher_form"):
            t_name = st.text_input("Full Name")
            t_user = st.text_input("Username")
            t_pass = st.text_input("Password", type="password")
            t_status = st.selectbox("Status", ["Active", "Deactivated"])
            if st.form_submit_button("Add Teacher"):
                if any(t['username'] == t_user for t in st.session_state.teachers):
                    st.error("Username already exists!")
                elif t_name and t_user and t_pass:
                    st.session_state.teachers.append({"name": t_name, "username": t_user, "password": t_pass, "status": t_status})
                    st.success(f"Teacher '{t_name}' added!")
                    st.rerun()
                else:
                    st.error("Fill all fields.")

    st.subheader("Teacher Directory")
    for i, t in enumerate(st.session_state.teachers):
        with st.container():
            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"**{t['name']}**  \n`@{t['username']}`")
            badge_cls = "badge-approved" if t['status'] == "Active" else "badge-rejected"
            c2.markdown(f"<span class='badge {badge_cls}'>{t['status']}</span>", unsafe_allow_html=True)
            b1, b2 = c3.columns(2)
            if t['status'] == "Active":
                if b1.button("Deactivate", key=f"deact_{i}"):
                    st.session_state.teachers[i]['status'] = "Deactivated"; st.rerun()
            else:
                if b1.button("Activate", key=f"act_{i}"):
                    st.session_state.teachers[i]['status'] = "Active"; st.rerun()
            if b2.button("🗑 Delete", key=f"del_t_{i}"):
                st.session_state.teachers.pop(i); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def admin_manage_subjects_page():
    if st.button("← Admin Dashboard"): go_to("admin_dashboard")
    st.title("Manage Subjects")

    col1, col2 = st.columns(2)
    with col1:
        new_perm = st.checkbox("Allow teachers to add subjects", value=st.session_state.settings['allow_teacher_add_subject'])
        if new_perm != st.session_state.settings['allow_teacher_add_subject']:
            st.session_state.settings['allow_teacher_add_subject'] = new_perm
            st.success("Permission updated.")
    with col2:
        req_approval = st.checkbox("Require admin approval for papers", value=st.session_state.settings['require_approval'])
        if req_approval != st.session_state.settings['require_approval']:
            st.session_state.settings['require_approval'] = req_approval
            st.success("Approval setting updated.")

    st.markdown("---")
    with st.expander("➕ Add New Subject"):
        with st.form("add_subject_form"):
            s_name = st.text_input("Subject Name")
            s_stream = st.selectbox("Stream", ["Computer Science", "Engineering", "Accounting", "School"])
            s_desc = st.text_area("Description (Optional)")
            if st.form_submit_button("Add Subject"):
                if [s for s in st.session_state.subjects if s['name'].lower() == s_name.lower() and s['stream'] == s_stream]:
                    st.error("Subject already exists in this stream.")
                elif s_name:
                    st.session_state.subjects.append({"name": s_name, "stream": s_stream, "description": s_desc})
                    st.success("Subject added!"); st.rerun()
                else:
                    st.error("Subject name required.")

    st.subheader("Subject Directory")
    streams = list(set(s['stream'] for s in st.session_state.subjects))
    for stream in sorted(streams):
        st.markdown(f"**{stream}**")
        stream_subs = [s for s in st.session_state.subjects if s['stream'] == stream]
        for idx, row in enumerate(stream_subs):
            global_idx = next(i for i, s in enumerate(st.session_state.subjects) if s['name'] == row['name'] and s['stream'] == stream)
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.write(f"📖 **{row['name']}** — {row['description']}")
            col2.write(f"*{row['stream']}*")
            if col3.button("🗑", key=f"del_s_{global_idx}"):
                st.session_state.subjects.pop(global_idx); st.rerun()


def admin_view_papers_page():
    if st.button("← Admin Dashboard"): go_to("admin_dashboard")
    st.title("Question Papers Review")

    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected", "Draft"])
    papers = list(reversed(st.session_state.paper_history))
    if status_filter != "All":
        papers = [p for p in papers if p.get('status', 'Draft') == status_filter]

    if not papers:
        st.info("No papers found.")
        return

    for p in papers:
        badge_map = {"Pending": "badge-pending", "Approved": "badge-approved", "Rejected": "badge-rejected", "Draft": "badge-draft"}
        badge_cls = badge_map.get(p.get('status', 'Draft'), "badge-draft")
        with st.expander(f"📄 {p['subject']}  |  by {p.get('teacher','?')}  |  {p.get('date','')}"):
            st.markdown(f"Stream: **{p['stream']}**  |  Marks: **{p['marks']}**  |  Difficulty: **{p.get('difficulty','N/A')}**")
            st.markdown(f"Status: <span class='badge {badge_cls}'>{p.get('status','Draft')}</span>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"👁 Review", key=f"rev_{p['id']}"):
                    st.session_state.generated_paper = p
                    go_to("view_paper")
            with c2:
                if p.get('status') == 'Pending':
                    if st.button("✅ Approve", key=f"appr_{p['id']}"):
                        for hp in st.session_state.paper_history:
                            if hp['id'] == p['id']:
                                hp['status'] = "Approved"
                                add_notification(hp['teacher'], f"Your paper '{hp['subject']}' was approved! ✅", "success")
                        st.rerun()
            with c3:
                if p.get('status') == 'Pending':
                    if st.button("❌ Reject", key=f"rej_{p['id']}"):
                        for hp in st.session_state.paper_history:
                            if hp['id'] == p['id']:
                                hp['status'] = "Rejected"
                                add_notification(hp['teacher'], f"Your paper '{hp['subject']}' was rejected. Please regenerate.", "error")
                        st.rerun()


# ------------------------------------------------------------------------------
# TEACHER PAGES
# ------------------------------------------------------------------------------
def dashboard_page():
    st.title(f"Welcome, {st.session_state.current_user} 👋")

    # Notifications
    user_msgs = st.session_state.notifications.get(st.session_state.current_user, [])
    if user_msgs:
        with st.expander(f"🔔 {len(user_msgs)} New Notification(s)", expanded=True):
            for m in reversed(user_msgs):
                fn = st.success if m['type'] == 'success' else (st.error if m['type'] == 'error' else st.info)
                fn(f"[{m.get('time','')}] {m['msg']}")
            if st.button("Clear All Notifications"):
                st.session_state.notifications[st.session_state.current_user] = []
                st.rerun()

    st.markdown("---")

    my_papers = [p for p in st.session_state.paper_history if p.get('teacher') == st.session_state.current_user]
    approved = len([p for p in my_papers if p.get('status') == 'Approved'])
    pending = len([p for p in my_papers if p.get('status') == 'Pending'])

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='stat-card'><div class='stat-value'>{len(my_papers)}</div><div class='stat-label'>Total Papers</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-card' style='border-left-color:#059669'><div class='stat-value' style='color:#059669'>{approved}</div><div class='stat-label'>Approved</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-card' style='border-left-color:#F59E0B'><div class='stat-value' style='color:#F59E0B'>{pending}</div><div class='stat-label'>Pending</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-card'><h3>✨ Create Paper</h3><p>Generate a new AI-powered question paper</p></div>", unsafe_allow_html=True)
        if st.button("Start Creating", key="btn_create"): go_to("create_paper")

    with col2:
        st.markdown(f"<div class='feature-card'><h3>📚 My History</h3><p>Access your {len(my_papers)} past papers</p></div>", unsafe_allow_html=True)
        if st.button("View History", key="btn_history"): go_to("history")

    with col3:
        if st.session_state.settings['allow_teacher_add_subject']:
            st.markdown("<div class='feature-card'><h3>➕ Add Subject</h3><p>Contribute a new subject to the database</p></div>", unsafe_allow_html=True)
            if st.button("Add Subject", key="btn_add_sub"): go_to("teacher_add_subject")
        else:
            st.markdown("<div class='feature-card' style='border-top-color:#CBD5E1'><h3>🔒 Add Subject</h3><p>Disabled by administrator</p></div>", unsafe_allow_html=True)
            st.button("Add Subject", disabled=True, key="btn_add_sub_d")

    st.markdown("---")
    logout_button()


def teacher_add_subject_page():
    if st.button("← Back to Dashboard"): go_to("dashboard")
    st.title("Add New Subject")

    with st.form("teacher_add_subject_form"):
        s_name = st.text_input("Subject Name")
        s_stream = st.selectbox("Stream", ["Computer Science", "Engineering", "Accounting", "School"])
        s_desc = st.text_area("Description (Optional)")
        if st.form_submit_button("Save Subject"):
            if not s_name:
                st.error("Subject name cannot be empty.")
            else:
                st.session_state.subjects.append({"name": s_name, "stream": s_stream, "description": s_desc})
                add_notification(st.session_state.current_user, f"Subject '{s_name}' added successfully.", "success")
                st.success("Subject saved!")
                time.sleep(0.8)
                go_to("dashboard")


def create_paper_page():
    if st.button("← Back to Dashboard"): go_to("dashboard")
    st.title("Create Question Paper")
    st.write("Configure the settings below and let AI generate your paper.")

    with st.form("paper_form"):
        col1, col2 = st.columns(2)
        with col1:
            stream = st.selectbox("Stream", ["Computer Science", "Engineering", "Accounting", "School"])
            difficulty = st.select_slider("Difficulty Level", options=["Easy", "Medium", "Hard"], value="Medium")
            exam_date = st.date_input("Exam Date")
            marks = st.number_input("Total Marks", min_value=20, max_value=200, value=100, step=10)

        with col2:
            stream_subjects = [s['name'] for s in st.session_state.subjects if s['stream'] == stream]
            if not stream_subjects:
                stream_subjects = ["General / Other"]
            subject = st.selectbox("Subject", stream_subjects)
            instructions = st.text_area("Exam Instructions", "All questions are compulsory.\nFigures to the right indicate full marks.")

            # Advanced options
            custom_topics = st.text_input(
                "Focus Topics (Optional)",
                placeholder="e.g., linked lists, binary trees, sorting"
            )
            bloom_options = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
            bloom_levels = st.multiselect(
                "Bloom's Taxonomy Levels",
                bloom_options,
                default=["Remember", "Understand", "Apply", "Analyze"]
            )

        submit = st.form_submit_button("✨ Generate with AI")

        if submit:
            with st.spinner("🤖 AI is generating your question paper..."):
                sections = generate_question_paper(
                    stream, subject, difficulty, marks,
                    custom_topics=custom_topics,
                    bloom_levels=bloom_levels
                )
                paper_data = {
                    "stream": stream, "subject": subject, "difficulty": difficulty,
                    "marks": marks, "date": exam_date, "sections": sections,
                    "instructions": instructions, "custom_topics": custom_topics,
                    "bloom_levels": bloom_levels, "status": "Draft",
                    "id": f"PP{int(time.time())}",
                    "teacher": st.session_state.current_user,
                    "created_at": datetime.now().strftime("%d %b %Y, %H:%M")
                }
                st.session_state.generated_paper = paper_data
                st.session_state.paper_history.append(paper_data)
                go_to("view_paper")


def view_paper_page():
    back_page = "admin_view_papers" if st.session_state.role == "admin" else "dashboard"
    if st.button(f"← Back"): go_to(back_page)

    paper = st.session_state.generated_paper
    if not paper:
        st.warning("No paper selected.")
        return

    institution = st.session_state.settings.get('institution_name', "Dr. D.Y. Patil College of Engineering and Technology")

    st.title("Question Paper Preview")

    # Paper Preview
    st.markdown("<div class='paper-wrapper'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='paper-header-block'>
        <div class='paper-inst'>{institution}</div>
        <div style='color:#6B7280; font-size:0.9rem;'>Department of {paper['stream']}  |  Semester Examination</div>
        <div class='paper-sub'>Subject: {paper['subject']}</div>
        <div class='paper-meta'>
            <span>📅 Date: {paper['date']}</span>
            <span>📊 Difficulty: {paper.get('difficulty','N/A')}</span>
            <span>🎯 Total Marks: {paper['marks']}</span>
        </div>
    </div>
    <div style='font-size:0.88rem; color:#6B7280; margin-bottom:12px;'>
        <strong>Instructions:</strong> {paper['instructions'].replace(chr(10), ' • ')}
    </div>
    """, unsafe_allow_html=True)

    for sec_key in ['A', 'B', 'C']:
        if sec_key not in paper['sections'] or paper['sections'][sec_key]['count'] == 0:
            continue
        sec = paper['sections'][sec_key]
        colors = {'A': '#1E3A8A', 'B': '#065F46', 'C': '#7C2D12'}
        color = colors.get(sec_key, '#1E3A8A')
        st.markdown(f"""
        <div class='section-header' style='background:{color};'>
            SECTION {sec_key} — {sec['name'].upper()}
        </div>
        <div style='font-size:0.85rem; color:#6B7280; margin-bottom:10px;'>
            Attempt all. Each question = {sec['marks_per_q']} marks
        </div>
        """, unsafe_allow_html=True)
        for i, q in enumerate(sec['questions'], 1):
            st.markdown(f"<div class='question-row'><strong>Q{i}.</strong> {q}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Actions ----
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.role == "teacher":
        pdf_bytes = create_pdf(paper, institution=institution)
        # Build text export
        text_content = f"{institution}\nSubject: {paper['subject']}\nDate: {paper['date']}  |  Marks: {paper['marks']}\n\nInstructions:\n{paper['instructions']}\n{'='*50}\n\n"
        for sec_key in ['A', 'B', 'C']:
            if sec_key in paper['sections'] and paper['sections'][sec_key]['count'] > 0:
                sec = paper['sections'][sec_key]
                text_content += f"SECTION {sec_key} – {sec['name']}\n(Each question = {sec['marks_per_q']} marks)\n\n"
                for i, q in enumerate(sec['questions'], 1):
                    text_content += f"Q{i}. {q}\n"
                text_content += "\n"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.download_button("📄 Download PDF", data=pdf_bytes, file_name=f"{paper['subject']}_Paper.pdf", mime="application/pdf", use_container_width=True)
        with c2:
            st.download_button("📝 Download TXT", data=text_content, file_name=f"{paper['subject']}_Paper.txt", mime="text/plain", use_container_width=True)
        with c3:
            if st.button("🔄 Regenerate", use_container_width=True):
                # Keep settings, regenerate
                with st.spinner("Regenerating..."):
                    new_sections = generate_question_paper(
                        paper['stream'], paper['subject'], paper['difficulty'], paper['marks'],
                        custom_topics=paper.get('custom_topics', ''),
                        bloom_levels=paper.get('bloom_levels', [])
                    )
                    # Update in place
                    for hp in st.session_state.paper_history:
                        if hp['id'] == paper['id']:
                            hp['sections'] = new_sections
                            hp['status'] = "Draft"
                            break
                    st.session_state.generated_paper['sections'] = new_sections
                    st.session_state.generated_paper['status'] = "Draft"
                st.rerun()
        with c4:
            status = paper.get('status', 'Draft')
            if status in ["Draft", "Rejected"]:
                if st.session_state.settings.get('require_approval', True):
                    if st.button("📤 Submit for Approval", use_container_width=True):
                        for hp in st.session_state.paper_history:
                            if hp['id'] == paper['id']:
                                hp['status'] = "Pending"
                        st.success("Submitted for admin approval!")
                        time.sleep(0.8)
                        go_to("dashboard")
                else:
                    if st.button("✅ Mark as Final", use_container_width=True):
                        for hp in st.session_state.paper_history:
                            if hp['id'] == paper['id']:
                                hp['status'] = "Approved"
                        st.success("Paper marked as final!")
                        time.sleep(0.8)
                        go_to("dashboard")
            else:
                badge_map = {"Pending": "badge-pending", "Approved": "badge-approved"}
                badge_cls = badge_map.get(status, "badge-draft")
                st.markdown(f"<br><span class='badge {badge_cls}'>Status: {status}</span>", unsafe_allow_html=True)

    elif st.session_state.role == "admin":
        st.subheader("Admin Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✅ Approve", use_container_width=True):
                for hp in st.session_state.paper_history:
                    if hp['id'] == paper['id']:
                        hp['status'] = "Approved"
                        add_notification(hp['teacher'], f"Paper '{hp['subject']}' approved! ✅", "success")
                st.success("Approved!")
                time.sleep(0.8)
                go_to("admin_view_papers")
        with c2:
            if st.button("❌ Reject", use_container_width=True):
                for hp in st.session_state.paper_history:
                    if hp['id'] == paper['id']:
                        hp['status'] = "Rejected"
                        add_notification(hp['teacher'], f"Paper '{hp['subject']}' was rejected. Please regenerate.", "error")
                st.success("Rejected!")
                time.sleep(0.8)
                go_to("admin_view_papers")
        with c3:
            pdf_bytes = create_pdf(paper, institution=institution)
            st.download_button("📄 Download PDF", data=pdf_bytes, file_name=f"{paper['subject']}_Admin.pdf", mime="application/pdf", use_container_width=True)


def history_page():
    if st.button("← Back to Dashboard"): go_to("dashboard")
    st.title("My Paper History")

    my_papers = [p for p in st.session_state.paper_history if p.get('teacher') == st.session_state.current_user]
    if not my_papers:
        st.info("No papers generated yet. Create your first one!")
        if st.button("Create Paper Now"): go_to("create_paper")
        return

    # Filter
    filter_status = st.selectbox("Filter", ["All", "Draft", "Pending", "Approved", "Rejected"])
    if filter_status != "All":
        my_papers = [p for p in my_papers if p.get('status', 'Draft') == filter_status]

    badge_map = {"Pending": "badge-pending", "Approved": "badge-approved", "Rejected": "badge-rejected", "Draft": "badge-draft"}

    for p in reversed(my_papers):
        badge_cls = badge_map.get(p.get('status', 'Draft'), "badge-draft")
        with st.expander(f"📄 {p['subject']}  |  {p['date']}  |  {p['marks']} Marks"):
            col1, col2 = st.columns([3, 1])
            col1.write(f"Stream: **{p['stream']}**  |  Difficulty: **{p.get('difficulty','N/A')}**  |  Created: *{p.get('created_at','N/A')}*")
            col1.markdown(f"<span class='badge {badge_cls}'>{p.get('status','Draft')}</span>", unsafe_allow_html=True)
            if col2.button("👁 View", key=f"view_{p['id']}"):
                st.session_state.generated_paper = p
                go_to("view_paper")


# ------------------------------------------------------------------------------
# ROUTING
# ------------------------------------------------------------------------------
def main():
    inject_custom_css()

    if not st.session_state.authenticated:
        login_page()
        return

    page = st.session_state.current_page
    routes = {
        "dashboard": dashboard_page,
        "create_paper": create_paper_page,
        "view_paper": view_paper_page,
        "history": history_page,
        "teacher_add_subject": teacher_add_subject_page,
        "admin_dashboard": admin_dashboard_page,
        "admin_manage_teachers": admin_manage_teachers_page,
        "admin_manage_subjects": admin_manage_subjects_page,
        "admin_view_papers": admin_view_papers_page,
    }

    handler = routes.get(page)
    if handler:
        handler()
    else:
        admin_dashboard_page() if st.session_state.role == "admin" else dashboard_page()


if __name__ == "__main__":
    main()
