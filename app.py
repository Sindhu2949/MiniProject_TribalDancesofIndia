from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import datetime
from metadata import dance_metadata
import sqlite3
import os
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ------------------ DATABASE SETUP ------------------
def init_db():
    if not os.path.exists('users.db'):
        conn = sqlite3.connect('users.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            content TEXT,
            media TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            comment TEXT,
            timestamp TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.commit()
        conn.close()

init_db()

# ------------------ BLOG/VLOG SYSTEM ------------------
@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        media = request.files['media']
        filename = ''
        if media:
            filename = f"{datetime.now().timestamp()}_{media.filename}"
            media.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (session['username'],))
        user_id = cur.fetchone()[0]
        cur.execute("INSERT INTO posts (user_id, title, content, media, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (user_id, title, content, filename, datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for('blog_feed'))
    return render_template('create_post.html')

@app.route('/blog_feed')
def blog_feed():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''SELECT posts.id, users.username, title, content, media, timestamp,
                          (SELECT COUNT(*) FROM likes WHERE post_id = posts.id) as like_count
                   FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.id DESC''')
    posts = cur.fetchall()
    conn.close()
    return render_template('blog_feed.html', posts=posts)

@app.route('/view_post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    if request.method == 'POST':
        comment = request.form['comment']
        cur.execute("SELECT id FROM users WHERE username=?", (session['username'],))
        user_id = cur.fetchone()[0]
        cur.execute("INSERT INTO comments (post_id, user_id, comment, timestamp) VALUES (?, ?, ?, ?)",
                    (post_id, user_id, comment, datetime.now()))
        conn.commit()

    cur.execute('''SELECT posts.id, users.username, title, content, media, timestamp
                   FROM posts JOIN users ON posts.user_id = users.id WHERE posts.id=?''', (post_id,))
    post = cur.fetchone()

    cur.execute('''SELECT users.username, comment, timestamp FROM comments
                   JOIN users ON comments.user_id = users.id WHERE post_id=? ORDER BY id DESC''', (post_id,))
    comments = cur.fetchall()
    conn.close()
    return render_template('view_post.html', post=post, comments=comments)

@app.route('/like/<int:post_id>')
def like(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (session['username'],))
    user_id = cur.fetchone()[0]
    cur.execute("SELECT * FROM likes WHERE post_id=? AND user_id=?", (post_id, user_id))
    if not cur.fetchone():
        cur.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for('view_post', post_id=post_id))

# ------------------ ROUTES ------------------

@app.route('/')
def root():
    return redirect(url_for('home')) if 'username' in session else redirect(url_for('login'))

@app.route('/index.html')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("index.html", username=session['username'])

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['username'] = username
            session['email'] = user[3]
            session['join_date'] = datetime.now().strftime("%Y-%m-%d")
            return redirect(url_for('home'))
        flash("Login failed. Invalid credentials.")
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = sqlite3.connect('users.db')
        try:
            conn.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
            conn.commit()
            flash("Registered successfully. Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
        finally:
            conn.close()
    return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("dashboard.html", username=session['username'])

@app.route('/quiz')
def quiz():
    if 'username' not in session:
        return redirect(url_for('login'))
    selected = random.sample(quiz_pool, 5)
    session['current_quiz'] = selected
    return render_template("quiz.html", questions=selected)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'username' not in session:
        return redirect(url_for('login'))
    questions = session.get('current_quiz', [])
    score = 0
    results = []
    for i, (q, correct, options) in enumerate(questions):
        ans = request.form.get(f'q{i}')
        if ans == correct:
            score += 1
        results.append((q, ans, correct))
    return render_template("quiz_result.html", score=score, total=len(questions), results=results)

@app.route('/shop')
def shop():
    if 'username' not in session:
        return redirect(url_for('login'))
    items = [
        ("Tribal Necklace", 250, url_for('static', filename='images/tribal_necklace.png')),
        ("Warli Print Saree", 700, url_for('static', filename='images/warli_saree.png')),
        ("Baiga Drum", 1200, url_for('static', filename='images/drum.png')),
        ("Chhau Mask", 450, url_for('static', filename='images/mask.png')),
        ("Santhal Beaded Anklets", 300, url_for('static', filename='images/anklet.png')),
        ("Bamboo Dance Sticks", 200, url_for('static', filename='images/bamboo_sticks.png')),
        ("Dokra Art Figurine", 900, url_for('static', filename='images/dokra.png')),
        ("Tribal Embroidered Bag", 350, url_for('static', filename='images/embroidered_bag.png')),
        ("Pattachitra Wall Art", 650, url_for('static', filename='images/pattachitra.png')),
        ("Tribal Face Paint Kit", 150, url_for('static', filename='images/face_paint.png')),
        ("Traditional Dhokra Bell", 400, url_for('static', filename='images/dhokra_bell.png')),
        ("Tassar Silk Shawl", 800, url_for('static', filename='images/tassar_shawl.png')),
        ("Handwoven Bamboo Hat", 180, url_for('static', filename='images/bamboo_hat.png')),
        ("Warrior Dance Headgear", 500, url_for('static', filename='images/headgear.png')),
        ("Tribal Slippers (Handcrafted)", 220, url_for('static', filename='images/slippers.png')),
        ("Banjara Mirror Work Cloth", 600, url_for('static', filename='images/banjara_mirror.png'))
    ]
    return render_template("shop.html", items=items)

@app.route('/add_to_cart', methods=["POST"])
def add_to_cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    item = request.form['item_name']
    price = int(request.form['price'])
    session.setdefault('cart', []).append({'item_name': item, 'price': price})
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)
    return render_template("cart.html", cart=cart_items, total=total)

@app.route('/remove_from_cart', methods=["POST"])
def remove_from_cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    index = int(request.form['index'])
    if 0 <= index < len(session.get('cart', [])):
        session['cart'].pop(index)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'username' not in session:
        return redirect(url_for('login'))
    total = sum(item['price'] for item in session.get('cart', []))
    if request.method == 'POST':
        name = request.form['name']
        method = request.form['payment_method']
        session.pop('cart', None)
        return redirect(url_for('payment_success', name=name, method=method))
    return render_template("payment.html", total=total)

@app.route('/payment_success')
def payment_success():
    if 'username' not in session:
        return redirect(url_for('login'))
    name = request.args.get('name')
    method = request.args.get('method')
    return render_template("payment_success.html", name=name, method=method)

@app.route('/workshops')
def workshops():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("workshop.html")

@app.route('/register_workshop', methods=['POST'])
def register_workshop():
    if 'username' not in session:
        return redirect(url_for('login'))
    name = request.form.get('workshop_name')
    session.setdefault('workshop_registrations', []).append({
        'workshop_name': name,
        'date': datetime.now().strftime("%Y-%m-%d"),
        'location': request.form.get('location', 'Unknown')
    })
    session.modified = True
    flash("Workshop registered.")
    return redirect(url_for('workshops'))

@app.route('/unregister_workshop', methods=['POST'])
def unregister_workshop():
    if 'username' not in session:
        return redirect(url_for('login'))
    name = request.form.get('workshop_name')
    session['workshop_registrations'] = [
        w for w in session.get('workshop_registrations', []) if w['workshop_name'] != name
    ]
    session.modified = True
    flash("Workshop unregistered.")
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("profile.html",
                           username=session['username'],
                           email=session.get('email', 'unknown'),
                           join_date=session.get('join_date', 'unknown'),
                           registered_workshops=session.get('workshop_registrations', []))

@app.route('/ar-vr')
def ar_vr():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("vr.html")

@app.route('/chatbot')
def chatbot():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("chatbot.html")

@app.route('/map')
def map_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("map.html")

@app.route('/dance_detail')
def dance_detail():
    if 'username' not in session:
        return redirect(url_for('login'))
    name = request.args.get('name')
    return render_template("dance_detail.html", name=name) if name else redirect(url_for('home'))

# ✅ SEARCH ROUTE FIXED
@app.route('/search')
def search_dance():
    if 'username' not in session:
        return redirect(url_for('login'))

    query = request.args.get('q', '').lower()
    region = request.args.get('region', '')
    festival = request.args.get('festival', '')
    significance = request.args.get('significance', '')

    results = {}
    for name, info in dance_metadata.items():
        if (not query or query in name.lower() or query in info['region'].lower() or any(query in fest.lower() for fest in info.get('festival', []))) and \
           (not region or info['region'] == region) and \
           (not festival or festival in info.get('festival', [])) and \
           (not significance or significance.lower() in info.get('significance_dance', '').lower()):
            results[name] = info

    all_names = list(dance_metadata.keys())
    all_regions = sorted(set(d['region'] for d in dance_metadata.values()))
    all_festivals = sorted(set(f for d in dance_metadata.values() for f in d.get('festival', [])))
    all_significance = sorted(set(d['significance_dance'] for d in dance_metadata.values() if 'significance_dance' in d))

    return render_template(
        'search.html',
        results=results,
        query=query,
        all_regions=all_regions,
        all_festivals=all_festivals,
        all_significance=all_significance,
        all_names=all_names,
        selected_region=region,
        selected_festival=festival,
        selected_significance=significance
    )
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------ QUIZ QUESTIONS ------------------
quiz_pool = [
    ("Which state is known for the Chhau dance?", "Odisha", ["Odisha", "Kerala", "Punjab", "Gujarat"]),
    ("Warli painting originates from which tribe?", "Maharashtra", ["Maharashtra", "Rajasthan", "Nagaland", "Sikkim"]),
    ("Ghoomar is a dance performed by which community?", "Rajasthan", ["Rajasthan", "Tamil Nadu", "Assam", "Goa"]),
    ("Which dance form uses bamboo sticks extensively?", "Mizoram", ["Mizoram", "Tripura", "Punjab", "Manipur"]),
    ("Siddi Dhamal is influenced by which origin?", "African", ["African", "European", "Mongolian", "Persian"]),
    ("Santhal dance is primarily found in?", "Jharkhand", ["Jharkhand", "Odisha", "Karnataka", "Telangana"]),
    ("Which tribe is known for the Baiga dance?", "Chhattisgarh", ["Chhattisgarh", "West Bengal", "Bihar", "Madhya Pradesh"]),
    ("Tharu dance is from which Indian region?", "Uttar Pradesh", ["Uttar Pradesh", "Nagaland", "Kerala", "Maharashtra"]),
    ("Toda tribal dance originates from?", "Tamil Nadu", ["Tamil Nadu", "Goa", "Assam", "Bihar"]),
    ("Bhil dance is popular in which state?", "Gujarat", ["Gujarat", "Punjab", "Tripura", "Uttarakhand"])
]

if __name__ == '__main__':
    app.run(debug=True)
