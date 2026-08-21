from database.connection import SessionLocal
from database.models import *


db = SessionLocal()


if db.query(User).first():
    print("Already seeded, skipping.")
    db.close()
    raise SystemExit(0)


user = User(
    name="Demo User"
)


db.add(user)


db.commit()


portfolio = Portfolio(
    name="Tech Growth Fund",
    user_id=user.id
)


db.add(portfolio)


db.commit()


holding1 = Holding(
    portfolio_id=portfolio.id,
    ticker="AAPL",
    quantity=10,
    purchase_price=180
)


holding2 = Holding(
    portfolio_id=portfolio.id,
    ticker="NVDA",
    quantity=5,
    purchase_price=120
)


db.add_all(
    [
        holding1,
        holding2
    ]
)


db.commit()


print("Seed completed")
