from datetime import datetime, timedelta

from django import forms
from django.conf import settings

OLDEST_LOGS_DATE = datetime.now() - timedelta(days=settings.LOG_RETENTION_DAYS)
TODAY = datetime.now()
DATEFMTST = "yyyy-mm-dd"


class RetrieveLogsForm(forms.Form):
    """
    Retrieve available logs
    """

    start_date = forms.DateField(
        input_formats=["%Y-%m-%d"],
        label="Start date",
        help_text=DATEFMTST,
        initial=OLDEST_LOGS_DATE,
        required=False,
    )
    end_date = forms.DateField(
        input_formats=["%Y-%m-%d"],
        label="End date",
        help_text=DATEFMTST,
        initial=TODAY,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].widget.attrs["class"] = "datepick"
        self.fields["end_date"].widget.attrs["class"] = "datepick"
