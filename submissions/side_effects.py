import logging

logger = logging.getLogger(__name__)


def send_confirmation(submission):
    """Fires after the submission row already exists — must never raise."""
    try:
        logger.info('CONFIRMATION SENT for submission %s (widget=%s)', submission.id, submission.widget_id)
        return True
    except Exception as exc:
        logger.error('Side effect failed for submission %s: %s', submission.id, exc)
        return False
    

# submissions/side_effects.py — temporarily
# def send_confirmation(submission):
#     raise Exception("simulated SMTP outage")