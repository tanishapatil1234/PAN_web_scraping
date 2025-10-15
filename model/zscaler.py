from __init__ import db

class ZscalerPress(db.Model):
    __tablename__ = 'zscaler_press'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    date = db.Column(db.String(50))
    url = db.Column(db.String(255))
    summary = db.Column(db.Text)
    category_detected = db.Column(db.String(50))
    keywords_matched = db.Column(db.Text)
    region_detected = db.Column(db.String(50))

    def __repr__(self):
        return f"<ZscalerPress {self.title}>"
