from datetime import datetime


def generate_tracking_id(report_id: int, submission_date: datetime) -> str:
    date_str = submission_date.strftime("%Y%m%d")
    return f"VS-{date_str}-{str(report_id).zfill(5)}".upper()
