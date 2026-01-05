"""
Celery tasks for response processing.
Maps to FR 3.3: Async Processing.
"""
import csv
import io
from celery import shared_task
from django.core.mail import send_mail


@shared_task
def export_responses_csv(survey_id: str, user_email: str):
    """
    Export survey responses to CSV and email to user.
    Runs asynchronously via Celery.
    """
    from apps.surveys.models import Survey
    from apps.responses.models import Response
    
    survey = Survey.objects.get(id=survey_id)
    responses = Response.objects.filter(survey=survey).select_related("user")
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    fields = survey.sections.prefetch_related("fields").values_list(
        "fields__id", "fields__label"
    )
    field_map = {str(fid): label for fid, label in fields if fid}
    writer.writerow(["Response ID", "User", "Submitted At"] + list(field_map.values()))
    
    # Data rows
    for response in responses:
        row = [
            str(response.id),
            response.user.email if response.user else "Anonymous",
            response.submitted_at.isoformat(),
        ]
        for field_id in field_map.keys():
            row.append(response.data.get(field_id, ""))
        writer.writerow(row)
    
    csv_content = output.getvalue()
    
    # Email the export (simplified - in production, upload to S3 and send link)
    send_mail(
        subject=f"Survey Export: {survey.title}",
        message=f"Your CSV export for '{survey.title}' is attached.",
        from_email="noreply@adsp.example.com",
        recipient_list=[user_email],
        html_message=f"<p>Export data:</p><pre>{csv_content[:1000]}...</pre>"
    )
    
    return f"Exported {responses.count()} responses"


@shared_task
def send_survey_invitation_batch(survey_id: str, email_list: list[str]):
    """
    Send survey invitation emails in batch.
    Runs asynchronously via Celery.
    """
    from apps.surveys.models import Survey
    
    survey = Survey.objects.get(id=survey_id)
    survey_url = f"https://adsp.example.com/s/{survey_id}"
    
    for email in email_list:
        send_mail(
            subject=f"You're invited: {survey.title}",
            message=f"Please complete this survey: {survey_url}",
            from_email="noreply@adsp.example.com",
            recipient_list=[email],
        )
    
    return f"Sent {len(email_list)} invitations"


@shared_task
def cleanup_stale_partial_responses(days_old: int = 30):
    """
    Remove partial responses older than specified days.
    Scheduled task for data hygiene.
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.responses.models import PartialResponse
    
    cutoff = timezone.now() - timedelta(days=days_old)
    deleted_count, _ = PartialResponse.objects.filter(last_updated__lt=cutoff).delete()
    
    return f"Deleted {deleted_count} stale partial responses"
