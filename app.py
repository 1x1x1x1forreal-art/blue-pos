
from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "bluepos_secret"

DB = "pos.db"

# ---------------- DB ----------------
def db():
    return sqlite3.connect(DB)

def init():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id TEXT,
        name TEXT,
        price REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT,
        time TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items(
        order_id INTEGER,
        name TEXT,
        qty INTEGER,
        price REAL
    )
    """)

    # seed
    cur.execute("INSERT INTO users VALUES ('cashier','1234','cashier')")
    cur.execute("INSERT INTO users VALUES ('kitchen','1234','kitchen')")

    cur.execute("INSERT INTO products VALUES ('1001','Burger',5.0)")
    cur.execute("INSERT INTO products VALUES ('1002','Fries',2.5)")
    cur.execute("INSERT INTO products VALUES ('1003','Coke',2.0)")

    con.commit()
    con.close()

init()

cart = []

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    err=""
    if request.method=="POST":
        u=request.form["u"]
        p=request.form["p"]

        con=db()
        cur=con.cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
        r=cur.fetchone()

        if r:
            session["role"]=r[0]
            return redirect("/cashier")
        err="wrong login"

    return render_template_string("""
    <body style="background:#0b1220;color:white;font-family:Arial;text-align:center">
    <h1>🔵 BLUE POS PRO</h1>

    <form method="POST">
        <input name="u" placeholder="user"><br><br>
        <input name="p" type="password" placeholder="pass"><br><br>
        <button>Login</button>
    </form>

    <p style="color:red">{{err}}</p>

    <p>cashier / 1234</p>
    <p>kitchen / 1234</p>
    </body>
    """, err=err)

# ---------------- CASHIER ----------------
@app.route("/cashier")
def cashier():
    con=db()
    cur=con.cursor()
    cur.execute("SELECT * FROM products")
    products=cur.fetchall()

    return render_template_string("""
    <body style="margin:0;font-family:Arial;background:#0b1220;color:white">

    <div style="background:#0d6efd;padding:15px;font-size:20px">
        🛒 BLUE POS CASHIER
    </div>

    <div style="display:flex">

    <div style="width:60%;padding:20px">
        <h2>Products</h2>

        {% for p in products %}
        <div style="background:#1e293b;padding:10px;margin:10px;border-radius:10px">
            {{p[1]}} - ${{p[2]}}
            <a href="/add/{{p[0]}}">
                <button style="float:right;background:#0d6efd;color:white;border:none;padding:5px 10px">
                    Add
                </button>
            </a>
        </div>
        {% endfor %}

    </div>

    <div style="width:40%;padding:20px;background:#111827">
        <h2>Cart</h2>

        {% for i in cart %}
            <div style="background:#1f2937;margin:5px;padding:10px;border-radius:8px">
                {{i['name']}} x{{i['qty']}}
            </div>
        {% endfor %}

        <br>

        <a href="/checkout">
            <button style="width:100%;padding:10px;background:#22c55e;color:white;border:none">
                CHECKOUT
            </button>
        </a>

        <br><br>

        <a href="/send">
            <button style="width:100%;padding:10px;background:#ef4444;color:white;border:none">
                SEND TO KITCHEN
            </button>
        </a>

    </div>

    </div>
    </body>
    """, products=products, cart=cart)

# ---------------- ADD ----------------
@app.route("/add/<pid>")
def add(pid):
    con=db()
    cur=con.cursor()
    cur.execute("SELECT name,price FROM products WHERE id=?", (pid,))
    p=cur.fetchone()

    for i in cart:
        if i["name"]==p[0]:
            i["qty"]+=1
            return redirect("/cashier")

    cart.append({"name":p[0],"qty":1,"price":p[1]})
    return redirect("/cashier")

# ---------------- CHECKOUT ----------------
@app.route("/checkout")
def checkout():
    con=db()
    cur=con.cursor()

    cur.execute("INSERT INTO orders(status,time) VALUES('NEW',?)", (str(datetime.now()),))
    oid=cur.lastrowid

    for i in cart:
        cur.execute("INSERT INTO items VALUES (?,?,?,?)",
                    (oid,i["name"],i["qty"],i["price"]))

    con.commit()
    cart.clear()

    return f"<h1>ORDER {oid} SENT</h1><a href='/cashier'>back</a>"

# ---------------- KITCHEN ----------------
@app.route("/kitchen")
def kitchen():
    con=db()
    cur=con.cursor()

    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders=cur.fetchall()

    html="<h1>🍔 KITCHEN</h1>"

    for o in orders:
        html+=f"<div style='border:1px solid #333;margin:10px;padding:10px'>"
        html+=f"<b>Order {o[0]} - {o[1]}</b><br>"

        cur.execute("SELECT name,qty FROM items WHERE order_id=?", (o[0],))
        items=cur.fetchall()

        for i in items:
            html+=f"- {i[0]} x{i[1]}<br>"

        html+="</div>"

    return html

# ---------------- SEND ----------------
@app.route("/send")
def send():
    return redirect("/checkout")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
