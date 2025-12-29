import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Render は接続文字列を環境変数で渡すのが基本 :contentReference[oaicite:3]{index=3}
# Render の DATABASE_URL は postgresql:// のことがあるので sqlalchemy 用に補正
db_url = os.environ.get("DATABASE_URL", "sqlite:///kakeibo.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    spent_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    memo = db.Column(db.Text, nullable=True)

@app.before_request
def ensure_tables():
    # 初回アクセス時にテーブル作成
    db.create_all()

@app.route("/", methods=["GET"])
def index():
    month = request.args.get("month") or date.today().strftime("%Y-%m")

    items = (
        Expense.query
        .filter(Expense.spent_date.like(f"{month}-%"))
        .order_by(Expense.spent_date.desc(), Expense.id.desc())
        .all()
    )

    total = sum(i.amount for i in items)

    categories = {}
    for i in items:
        categories[i.category] = categories.get(i.category, 0) + i.amount

    return render_template("index.html", month=month, items=items, total=total, categories=categories)

@app.route("/add", methods=["POST"])
def add():
    spent_date = request.form.get("spent_date") or date.today().isoformat()
    category = request.form.get("category") or "未分類"
    memo = request.form.get("memo", "")

    try:
        amount = int(request.form.get("amount"))
    except:
        return redirect(url_for("index"))

    e = Expense(spent_date=spent_date, amount=amount, category=category, memo=memo)
    db.session.add(e)
    db.session.commit()

    return redirect(url_for("index", month=spent_date[:7]))

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    e = Expense.query.get(item_id)
    if e:
        db.session.delete(e)
        db.session.commit()
    return redirect(request.referrer or url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
