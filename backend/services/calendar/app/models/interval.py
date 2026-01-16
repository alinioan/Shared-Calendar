from ..db import db

class Interval(db.Model):
    __tablename__ = "interval"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
