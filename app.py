"""
Artéum — a small site where people post paintings (their own or famous works)
along with a written report about the piece.

Real database (SQLite via SQLAlchemy), real accounts (Flask-Login + hashed
passwords), follow / like, a full painting detail page, and a real light /
dark mode toggle.

Run it:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import re
import secrets
import uuid
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "avif", "tif", "tiff", "heic", "heif"}
AVATAR_PALETTE = ["#B8860B", "#6B4226", "#8E6FA6", "#5B7B63", "#9C5B3C", "#4A5B7A"]

# ----------------------------------------------------------------- i18n --
# Small, dictionary-based translation of the site's chrome (nav, buttons,
# page titles). Painting titles/reports are user-written and untranslated.
TRANSLATIONS = {
    "en": {
        "nav_home": "Home", "nav_explore": "Explore", "nav_gallery": "My gallery",
        "nav_profile": "Profile", "nav_messages": "Messages", "nav_settings": "Settings",
        "compose": "Add a painting", "theme_dark": "Dark mode", "theme_light": "Light mode",
        "signup_cta": "Sign up", "login_cta": "Log in", "logout": "Log out",
        "home_title": "Fresh off the easel", "home_sub": "Paintings from artists you follow — with a report on each.",
        "mid_follow_title": "People to follow",
        "explore_title": "Explore", "explore_sub": "Every painting posted on Artéum, newest first.",
        "gallery_title": "My gallery", "gallery_sub": "Paintings you've added to Artéum.",
        "empty_home": "Follow a few artists to fill this feed, or explore everything people have posted →",
        "empty_gallery": "You haven't added a painting yet. Add your first one →",
        "empty_explore": "No paintings yet.",
        "rail_artists": "Recommended for you", "rail_trending": "Trending this week",
        "nav_activity": "Activity", "activity_title": "Activity", "activity_sub": "Likes, reposts and new followers, in one place.",
        "no_activity": "Nothing yet — once someone likes, reposts or follows you, it shows up here.",
        "act_liked": "liked your painting", "act_followed": "started following you",
        "act_reposted": "reposted your painting",
        "repost": "Repost", "reposted_label": "Reposted", "reposted_by_prefix": "reposted",
        "attach_image": "Attach image", "photo_label": "📷 Photo",
        "search_placeholder": "Search Artéum", "search_title": "Search",
        "search_sub": "Results for", "no_results": "No matches found.",
        "tab_posts": "Posts", "tab_likes": "Likes", "tab_following": "Following",
        "share_painting": "Share a painting…", "no_likes_yet": "No liked paintings yet.",
        "no_following_yet": "Not following anyone yet.",
        "follow": "Follow", "following": "Following", "message_btn": "Message",
        "followers_label": "followers",
        "nothing_posted": "Nothing posted yet.",
        "rail_no_suggestions": "No one to suggest yet.", "rail_no_trending": "Nothing trending yet.",
        "login_title": "Welcome back", "login_sub": "Log in to add paintings, like and follow artists.",
        "field_identifier": "Username or email", "field_password": "Password",
        "btn_login": "Log in", "new_to_arteum": "New to Artéum?", "create_account": "Create an account",
        "signup_title": "Join Artéum", "signup_sub": "Post paintings — yours or famous ones — and write reports about them.",
        "field_username": "Username", "field_email": "Email", "btn_signup": "Create account",
        "already_have_account": "Already have an account?",
        "add_title": "Add a painting", "add_sub": "Upload a famous painting or one of your own, and write a short report about it.",
        "field_title": "Painting title", "field_painter": "Painted by", "field_year": "Year painted",
        "field_medium": "Medium", "field_image": "Image of the painting", "choose_image": "Choose image",
        "no_file_chosen": "No file chosen", "field_report": "Report / notes about the painting",
        "btn_add": "Add to Artéum",
        "settings_title": "Settings", "settings_sub": "Your account preferences.",
        "field_language": "Language", "btn_save": "Save",
        "messages_title": "Messages", "messages_sub": "Direct conversations with other artists.",
        "no_conversations": "No conversations yet. Visit a profile and send a message to start one.",
        "field_message": "Write a message…", "btn_send": "Send",
    },
    "ar": {
        "nav_home": "الرئيسية", "nav_explore": "استكشاف", "nav_gallery": "معرضي",
        "nav_profile": "الملف الشخصي", "nav_messages": "الرسائل", "nav_settings": "الإعدادات",
        "compose": "أضف لوحة", "theme_dark": "الوضع الداكن", "theme_light": "الوضع الفاتح",
        "signup_cta": "إنشاء حساب", "login_cta": "تسجيل الدخول", "logout": "تسجيل الخروج",
        "home_title": "طازجة من المرسم", "home_sub": "لوحات من فنانين تتابعهم — مع تقرير عن كل واحدة.",
        "mid_follow_title": "أشخاص لمتابعتهم",
        "explore_title": "استكشاف", "explore_sub": "كل لوحة نُشرت على Artéum، الأحدث أولاً.",
        "gallery_title": "معرضي", "gallery_sub": "اللوحات اللي أضفتها إلى Artéum.",
        "empty_home": "تابع بعض الفنانين لتمتلئ صفحتك، أو استكشف كل ما نشره الآخرون ←",
        "empty_gallery": "لم تضف لوحة بعد. أضف أول لوحة لك ←",
        "empty_explore": "لا توجد لوحات بعد.",
        "rail_artists": "موصى بهم لك", "rail_trending": "الأكثر تفاعلاً هذا الأسبوع",
        "nav_activity": "النشاط", "activity_title": "النشاط", "activity_sub": "الإعجابات وإعادة النشر والمتابعون الجدد، في مكان واحد.",
        "no_activity": "لا شيء بعد — لما حد يعجب أو يعيد نشر أو يتابعك، بيظهر هنا.",
        "act_liked": "أعجب بلوحتك", "act_followed": "بدأ متابعتك",
        "act_reposted": "أعاد نشر لوحتك",
        "repost": "إعادة نشر", "reposted_label": "أُعيد نشرها", "reposted_by_prefix": "أعاد نشر",
        "attach_image": "إرفاق صورة", "photo_label": "📷 صورة",
        "search_placeholder": "ابحث في Artéum", "search_title": "بحث",
        "search_sub": "نتائج عن", "no_results": "لا توجد نتائج.",
        "tab_posts": "المنشورات", "tab_likes": "الإعجابات", "tab_following": "المتابَعون",
        "share_painting": "شارك لوحة…", "no_likes_yet": "لا توجد لوحات معجب بها بعد.",
        "no_following_yet": "لا يتابع أحدًا بعد.",
        "follow": "متابعة", "following": "متابَع", "message_btn": "مراسلة",
        "followers_label": "متابعون",
        "nothing_posted": "لا يوجد منشور بعد.",
        "rail_no_suggestions": "لا يوجد أحد لاقتراحه بعد.", "rail_no_trending": "لا يوجد شيء رائج بعد.",
        "login_title": "أهلاً بعودتك", "login_sub": "سجّل الدخول لإضافة لوحات، والإعجاب، ومتابعة الفنانين.",
        "field_identifier": "اسم المستخدم أو البريد الإلكتروني", "field_password": "كلمة المرور",
        "btn_login": "تسجيل الدخول", "new_to_arteum": "جديد على Artéum؟", "create_account": "أنشئ حسابًا",
        "signup_title": "انضم إلى Artéum", "signup_sub": "انشر لوحات — خاصة بك أو مشهورة — واكتب تقارير عنها.",
        "field_username": "اسم المستخدم", "field_email": "البريد الإلكتروني", "btn_signup": "إنشاء الحساب",
        "already_have_account": "لديك حساب بالفعل؟",
        "add_title": "أضف لوحة", "add_sub": "ارفع لوحة مشهورة أو من رسمك، واكتب تقريرًا قصيرًا عنها.",
        "field_title": "عنوان اللوحة", "field_painter": "رسمها", "field_year": "سنة الرسم",
        "field_medium": "الخامة", "field_image": "صورة اللوحة", "choose_image": "اختر صورة",
        "no_file_chosen": "لم يتم اختيار ملف", "field_report": "تقرير / ملاحظات عن اللوحة",
        "btn_add": "أضف إلى Artéum",
        "settings_title": "الإعدادات", "settings_sub": "تفضيلات حسابك.",
        "field_language": "اللغة", "btn_save": "حفظ",
        "messages_title": "الرسائل", "messages_sub": "محادثات مباشرة مع فنانين آخرين.",
        "no_conversations": "لا توجد محادثات بعد. زر أحد الملفات الشخصية وأرسل رسالة لتبدأ واحدة.",
        "field_message": "اكتب رسالة…", "btn_send": "إرسال",
    },
}

# Set ARTEUM_ENV=production on the server (see DEPLOY.md). Locally, leave it unset.
IS_PRODUCTION = os.environ.get("ARTEUM_ENV", "development").lower() == "production"
USERNAME_RE = re.compile(r"^[\w.\-]{3,30}$")


def _load_secret_key():
    """SECRET_KEY env var if set, otherwise a random key saved next to app.py."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    key_file = os.path.join(BASE_DIR, ".secret_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    try:
        with open(key_file, "w", encoding="utf-8") as f:
            f.write(key)
    except OSError:
        pass
    return key


def _database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):  # some hosts still hand out the old scheme
        url = url.replace("postgres://", "postgresql://", 1)
    return url or "sqlite:///" + os.path.join(BASE_DIR, "arteum.db")


app = Flask(__name__)
app.config["SECRET_KEY"] = _load_secret_key()
app.config["SQLALCHEMY_DATABASE_URI"] = _database_url()
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 280}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB per upload
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION  # cookies only over HTTPS when deployed

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = None  # a plain redirect to the login page, no "please log in" flash


# ---------------------------------------------------------------- models --

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_filename = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(5), default="en", nullable=False)
    last_activity_view = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    paintings = db.relationship("Painting", backref="artist", lazy="select",
                                 cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def avatar_color(self):
        return AVATAR_PALETTE[sum(ord(c) for c in self.username) % len(AVATAR_PALETTE)]

    def is_following(self, other_user):
        return Follow.query.filter_by(follower_id=self.id, followee_id=other_user.id).first() is not None


class Painting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    painter_name = db.Column(db.String(120), nullable=False)  # who painted it (may differ from poster)
    year = db.Column(db.String(20))
    medium = db.Column(db.String(80))
    report = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    likes = db.relationship("Like", backref="painting", lazy="select", cascade="all, delete-orphan")
    reposts = db.relationship("Repost", backref="painting", lazy="select", cascade="all, delete-orphan")

    def liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return any(l.user_id == user.id for l in self.likes)

    def is_reposted_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return any(r.user_id == user.id for r in self.reposts)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    painting_id = db.Column(db.Integer, db.ForeignKey("painting.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "painting_id"),)


class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    followee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("follower_id", "followee_id"),)


class Repost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    painting_id = db.Column(db.Integer, db.ForeignKey("painting.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "painting_id"),)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --------------------------------------------------------------- helpers --

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_lang():
    if current_user.is_authenticated:
        return current_user.language or "en"
    return session.get("lang", "en")


@app.context_processor
def inject_i18n():
    lang = current_lang()
    strings = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return {"t": lambda key: strings.get(key, key), "lang": lang}


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code not in TRANSLATIONS:
        lang_code = "en"
    session["lang"] = lang_code
    if current_user.is_authenticated:
        current_user.language = lang_code
        db.session.commit()
    return redirect(request.referrer or url_for("index"))


def is_safe_next(target):
    """Only allow redirects to paths on this site (blocks ?next=https://evil.com)."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc


@app.route("/healthz")
def healthz():
    return "ok"


def save_upload(file_storage):
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return filename


# ---------------------------------------------------------------- routes --

def build_feed_items(user_ids=None, include_reposts=True):
    """Original paintings + reposts by the given users (or everyone if None),
    newest first, each as {'painting', 'reposted_by'}."""
    q = Painting.query
    if user_ids is not None:
        q = q.filter(Painting.user_id.in_(user_ids))
    items = [{"painting": p, "reposted_by": None, "sort_time": p.created_at} for p in q.all()]

    if include_reposts:
        rq = Repost.query
        if user_ids is not None:
            rq = rq.filter(Repost.user_id.in_(user_ids))
        for r in rq.all():
            p = db.session.get(Painting, r.painting_id)
            if p:
                items.append({"painting": p, "reposted_by": db.session.get(User, r.user_id),
                              "sort_time": r.created_at})

    items.sort(key=lambda i: i["sort_time"] or datetime.min, reverse=True)
    return items


@app.route("/")
@login_required
def index():
    followed_ids = [f.followee_id for f in Follow.query.filter_by(follower_id=current_user.id)]
    ids = followed_ids + [current_user.id]
    items = build_feed_items(ids)
    empty_hint = "explore" if not items else None
    return render_template("index.html", items=items, page="home",
                            empty_hint=empty_hint, show_rail=True,
                            **rail_context())


@app.route("/explore")
@login_required
def explore():
    items = build_feed_items(None)
    return render_template("index.html", items=items, page="explore",
                            empty_hint=None, show_rail=True, **rail_context())


@app.route("/gallery")
@login_required
def gallery():
    items = build_feed_items([current_user.id])
    return render_template("index.html", items=items, page="gallery",
                            empty_hint=None, show_rail=False)


@app.route("/painting/<int:painting_id>")
@login_required
def painting_detail(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    return render_template("painting.html", p=painting, page="painting", show_rail=False)


@app.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    tab = request.args.get("tab", "posts")
    if tab not in ("posts", "likes", "following"):
        tab = "posts"

    items, following_users = [], []
    if tab == "posts":
        items = build_feed_items([user.id])
    elif tab == "likes":
        liked_ids = [l.painting_id for l in Like.query.filter_by(user_id=user.id)]
        liked = (Painting.query.filter(Painting.id.in_(liked_ids))
                 .order_by(Painting.created_at.desc()).all()) if liked_ids else []
        items = [{"painting": p, "reposted_by": None} for p in liked]
    elif tab == "following":
        followee_ids = [f.followee_id for f in Follow.query.filter_by(follower_id=user.id)]
        following_users = User.query.filter(User.id.in_(followee_ids)).all() if followee_ids else []

    follower_count = Follow.query.filter_by(followee_id=user.id).count()
    following_count = Follow.query.filter_by(follower_id=user.id).count()
    painting_count = Painting.query.filter_by(user_id=user.id).count()
    return render_template("profile.html", profile_user=user, items=items,
                            following_users=following_users, tab=tab,
                            follower_count=follower_count, following_count=following_count,
                            painting_count=painting_count,
                            page="profile", show_rail=False)


def rail_context():
    suggested = []
    if current_user.is_authenticated:
        followed_ids = {f.followee_id for f in Follow.query.filter_by(follower_id=current_user.id)}
        followed_ids.add(current_user.id)
        suggested = User.query.filter(User.id.notin_(list(followed_ids))).limit(4).all()
    else:
        suggested = User.query.limit(4).all()
    trending = (Painting.query.outerjoin(Like)
                .group_by(Painting.id)
                .order_by(db.func.count(Like.id).desc())
                .limit(4).all())
    return {"suggested": suggested, "trending": trending}


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        title = request.form.get("title", "").strip() or "Untitled"
        painter_name = request.form.get("painter_name", "").strip() or current_user.username
        year = request.form.get("year", "").strip()
        medium = request.form.get("medium", "").strip()
        report = request.form.get("report", "").strip()
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("Please choose an image of the painting.")
            return redirect(url_for("add"))
        if not allowed_file(file.filename):
            flash("That file type isn't supported. Use jpg, png, gif or webp.")
            return redirect(url_for("add"))

        filename = save_upload(file)
        painting = Painting(user_id=current_user.id, title=title, painter_name=painter_name,
                             year=year, medium=medium, report=report, filename=filename)
        db.session.add(painting)
        db.session.commit()
        flash("Added to the feed.")
        return redirect(url_for("gallery"))

    return render_template("add.html", page="add", show_rail=False)


@app.route("/painting/<int:painting_id>/delete", methods=["POST"])
@login_required
def delete_painting(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    if painting.user_id != current_user.id:
        flash("You can only remove your own paintings.")
        return redirect(request.referrer or url_for("index"))
    path = os.path.join(app.config["UPLOAD_FOLDER"], painting.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(painting)
    db.session.commit()
    return redirect(request.referrer or url_for("gallery"))


@app.route("/painting/<int:painting_id>/like", methods=["POST"])
@login_required
def like_painting(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    existing = Like.query.filter_by(user_id=current_user.id, painting_id=painting.id).first()
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Like(user_id=current_user.id, painting_id=painting.id))
    db.session.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/painting/<int:painting_id>/repost", methods=["POST"])
@login_required
def repost_painting(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    existing = Repost.query.filter_by(user_id=current_user.id, painting_id=painting.id).first()
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Repost(user_id=current_user.id, painting_id=painting.id))
    db.session.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/profile/<username>/follow", methods=["POST"])
@login_required
def follow(username):
    target = User.query.filter_by(username=username).first_or_404()
    if target.id != current_user.id:
        existing = Follow.query.filter_by(follower_id=current_user.id, followee_id=target.id).first()
        if existing:
            db.session.delete(existing)
        else:
            db.session.add(Follow(follower_id=current_user.id, followee_id=target.id))
        db.session.commit()
    return redirect(url_for("profile", username=username))


@app.route("/account/avatar", methods=["POST"])
@login_required
def update_avatar():
    file = request.files.get("avatar")
    if not file or file.filename == "" or not allowed_file(file.filename):
        flash("Please choose a valid image (jpg, png, gif or webp).")
        return redirect(url_for("profile", username=current_user.username))

    old = current_user.avatar_filename
    current_user.avatar_filename = save_upload(file)
    db.session.commit()
    if old:
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], old)
        if os.path.exists(old_path):
            os.remove(old_path)
    return redirect(url_for("profile", username=current_user.username))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        lang_code = request.form.get("language", "en")
        if lang_code not in TRANSLATIONS:
            lang_code = "en"
        current_user.language = lang_code
        session["lang"] = lang_code
        db.session.commit()
        flash("Saved.")
        return redirect(url_for("settings"))
    return render_template("settings.html", page="settings", show_rail=False)


@app.route("/messages")
@login_required
def messages_inbox():
    mine = (Message.query
            .filter((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id))
            .order_by(Message.created_at.desc()).all())
    latest_by_partner = {}
    for m in mine:
        partner_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        if partner_id not in latest_by_partner:
            latest_by_partner[partner_id] = m
    partners = []
    for partner_id, last_msg in latest_by_partner.items():
        partner = db.session.get(User, partner_id)
        if partner:
            unread = Message.query.filter_by(sender_id=partner_id, recipient_id=current_user.id, is_read=False).count()
            partners.append({"user": partner, "last": last_msg, "unread": unread})
    partners.sort(key=lambda p: p["last"].created_at, reverse=True)
    return render_template("messages_inbox.html", partners=partners, page="messages", show_rail=False)


@app.route("/messages/<username>", methods=["GET", "POST"])
@login_required
def messages_thread(username):
    partner = User.query.filter_by(username=username).first_or_404()
    if partner.id == current_user.id:
        return redirect(url_for("messages_inbox"))

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        image_filename = None
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            image_filename = save_upload(file)
        if body or image_filename:
            db.session.add(Message(sender_id=current_user.id, recipient_id=partner.id,
                                    body=body or None, image_filename=image_filename))
            db.session.commit()
        return redirect(url_for("messages_thread", username=username))

    thread = (Message.query.filter(
                or_(
                    and_(Message.sender_id == current_user.id, Message.recipient_id == partner.id),
                    and_(Message.sender_id == partner.id, Message.recipient_id == current_user.id),
                ))
              .order_by(Message.created_at.asc()).all())

    unread = [m for m in thread if m.recipient_id == current_user.id and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return render_template("messages_thread.html", partner=partner, thread=thread,
                            page="messages", show_rail=False)


def unread_message_count():
    if not current_user.is_authenticated:
        return 0
    return Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()


def _activity_items(user):
    """Likes on this user's paintings + new followers, newest first."""
    items = []
    painting_ids = [p.id for p in user.paintings]
    if painting_ids:
        likes = (Like.query.filter(Like.painting_id.in_(painting_ids))
                 .filter(Like.user_id != user.id)
                 .order_by(Like.id.desc()).limit(30).all())
        for l in likes:
            actor = db.session.get(User, l.user_id)
            painting = db.session.get(Painting, l.painting_id)
            if actor and painting:
                items.append({"kind": "like", "actor": actor, "painting": painting,
                              "created_at": painting.created_at})
    follows = (Follow.query.filter_by(followee_id=user.id)
               .order_by(Follow.id.desc()).limit(30).all())
    for f in follows:
        actor = db.session.get(User, f.follower_id)
        if actor:
            items.append({"kind": "follow", "actor": actor, "painting": None,
                          "created_at": actor.joined_at})
    if painting_ids:
        reposts = (Repost.query.filter(Repost.painting_id.in_(painting_ids))
                   .filter(Repost.user_id != user.id)
                   .order_by(Repost.id.desc()).limit(30).all())
        for r in reposts:
            actor = db.session.get(User, r.user_id)
            painting = db.session.get(Painting, r.painting_id)
            if actor and painting:
                items.append({"kind": "repost", "actor": actor, "painting": painting,
                              "created_at": r.created_at})
    items.sort(key=lambda i: i["created_at"] or datetime.min, reverse=True)
    return items[:30]


def has_new_activity():
    if not current_user.is_authenticated:
        return False
    items = _activity_items(current_user)
    if not items:
        return False
    last_seen = current_user.last_activity_view
    if not last_seen:
        return True
    return any((i["created_at"] or datetime.min) > last_seen for i in items)


app.jinja_env.globals["unread_message_count"] = unread_message_count
app.jinja_env.globals["has_new_activity"] = has_new_activity


@app.route("/activity")
@login_required
def activity():
    items = _activity_items(current_user)
    current_user.last_activity_view = datetime.utcnow()
    db.session.commit()
    return render_template("activity.html", items=items, page="activity", show_rail=False)


@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    users, paintings = [], []
    if q:
        like = f"%{q}%"
        users = User.query.filter(User.username.ilike(like)).limit(10).all()
        paintings = (Painting.query.filter(or_(Painting.title.ilike(like), Painting.painter_name.ilike(like)))
                     .order_by(Painting.created_at.desc()).limit(10).all())
    return render_template("search.html", q=q, users=users, paintings=paintings,
                            page="search", show_rail=False)


@app.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return {"users": [], "paintings": []}
    like = f"%{q}%"
    users = User.query.filter(User.username.ilike(like)).limit(5).all()
    paintings = (Painting.query.filter(or_(Painting.title.ilike(like), Painting.painter_name.ilike(like)))
                 .limit(5).all())
    return {
        "users": [{"username": u.username, "url": url_for("profile", username=u.username)} for u in users],
        "paintings": [{"title": p.title, "painter_name": p.painter_name,
                        "url": url_for("painting_detail", painting_id=p.id)} for p in paintings],
    }


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Fill in every field to create an account.")
        elif not USERNAME_RE.match(username):
            flash("Username must be 3-30 characters: letters, numbers, dots, dashes or underscores.")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
        elif User.query.filter_by(username=username).first():
            flash("That username is taken.")
        elif User.query.filter_by(email=email).first():
            flash("An account already uses that email.")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("index"))

    return render_template("signup.html", page="signup", show_rail=False)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = (User.query.filter_by(username=identifier).first()
                or User.query.filter_by(email=identifier.lower()).first())
        if user and user.check_password(password):
            login_user(user)
            next_url = request.args.get("next", "")
            return redirect(next_url if is_safe_next(next_url) else url_for("index"))
        flash("That username/email and password don't match.")

    return render_template("login.html", page="login", show_rail=False)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


def seed_demo_data():
    """Adds one demo artist + painting so the feed isn't empty on first run."""
    if User.query.count() > 0:
        return
    demo = User(username="mira", email="mira@example.com")
    demo.set_password("password123")
    db.session.add(demo)
    db.session.commit()

    starry_night_report = (
        "تُعد «ليلة النجوم» واحدة من أشهر لوحات الفنان الهولندي فنسنت فان غوخ، "
        "ومن أبرز الأعمال التي ميّزت مرحلة ما بعد الانطباعية.\n\n"
        "رسم فان غوخ اللوحة في يونيو عام 1889 أثناء إقامته في مصحّ سان بول دو موزول "
        "في سان ريمي دو بروفانس، جنوب فرنسا. وقد استوحى العمل من المنظر الذي كان يراه "
        "من نافذة غرفته، لكنه لم يكتفِ بنقل المشهد كما هو؛ بل أعاد تشكيله من خلال "
        "خياله وأسلوبه التعبيري المميز.\n\n"
        "يسيطر على الجزء العلوي من اللوحة سماء زرقاء عميقة تتخللها دوامات وخطوط من "
        "الألوان. تظهر هلال مضيء في الجهة اليمنى، بينما يلمع كوكب الزهرة بالقرب من "
        "منتصف السماء. تبدو النجوم محاطة بهالات من الضوء، وكأنها تنبض أو تتحرك داخل "
        "السماء.\n\n"
        "في الأسفل تظهر قرية هادئة محاطة بالتلال الداكنة، بينما ترتفع في المقدمة "
        "شجرة سرو طويلة وداكنة تشكل رابطًا بصريًا قويًا بين الأرض والسماء. ومن أكثر "
        "ما يلفت النظر هو التناقض بين المشهدين: القرية هادئة وساكنة، بينما السماء "
        "تبدو حية ومتحركة.\n\n"
        "تتميز اللوحة باستخدامها القوي للألوان، خصوصًا درجات الأزرق والأصفر. لكن "
        "الألوان ليست العنصر الوحيد الذي يمنح العمل طاقته؛ فالفرشاة نفسها تصبح جزءًا "
        "من التعبير. استخدم فان غوخ ضربات فرشاة واضحة وسميكة، وهي تقنية تُعرف باسم "
        "الإمباستو (Impasto)، حيث توضع طبقات من الطلاء بكثافة على سطح القماش.\n\n"
        "بعد وفاة فان غوخ، انتقلت اللوحة إلى شقيقه ثيو فان غوخ، ثم مرت عبر عدة "
        "مجموعات فنية قبل أن تصل إلى متحف الفن الحديث في نيويورك، وفي عام 1941 "
        "أصبحت جزءًا من مجموعة المتحف من خلال وصية ليلي ب. بليس.\n\n"
        "منظور Artéum: «ليلة النجوم» تذكرنا بأن الفن لا يحتاج دائمًا إلى إعادة إنتاج "
        "العالم كما تراه العين. أحيانًا، الطريقة التي يغيّر بها الفنان الواقع تكشف "
        "لنا عنه أكثر مما يفعله الواقع نفسه."
    )
    db.session.add(Painting(
        user_id=demo.id, title="ليلة النجوم", painter_name="Vincent van Gogh",
        year="1889", medium="Oil on canvas", filename="starry_night.png",
        report=starry_night_report,
    ))
    db.session.commit()


# Runs on import, so it also works under gunicorn / a WSGI host (not just `python app.py`).
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    if not IS_PRODUCTION:
        with app.app_context():
            seed_demo_data()  # demo account only for local development
    app.run(debug=not IS_PRODUCTION)
