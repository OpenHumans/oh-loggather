from datetime import datetime, timezone
import io

from django.conf import settings

from celery import shared_task
from celery.utils.log import get_task_logger

from ohapi.api import get_all_results, upload_stream

from openhumans.models import OpenHumansMember

logger = get_task_logger(__name__)


def serialize_accesslogs(api_endpoint, oh_member, access_token, start_date, end_date):
    """
    Groups logs by project, then converts from dict to csv, and finally uploads the
    resultant csv files to aws.
    """
    accesslog_api_url = "{0}/data-management/{1}/?access_token={2}".format(
        settings.OPENHUMANS_OH_BASE_URL, api_endpoint, oh_member.get_access_token()
    )
    if start_date:
        accesslog_api_url = "{0}&start_date={1}".format(accesslog_api_url, start_date)
    if end_date:
        accesslog_api_url = "{0}&end_date={1}".format(accesslog_api_url, end_date)
    if api_endpoint == "newdatafileaccesslog":
        access_point = "open-humans"
        headers = [
            "date",
            "ip_address",
            "user",
            "datafile_id",
            "datafile_source",
            "datafile_created",
            "datafile_user_id",
            "datafile_basename",
            "datafile_download_url",
            "key_id",
            "key_key",
            "key_created",
            "key_project_id",
            "key_datafile_id",
            "key_access_token",
            "key_key_creation_ip_address",
        ]
    else:
        access_point = "aws"
        headers = [
            "time",
            "remote_ip",
            "request_id",
            "operation",
            "bucket_key",
            "request_uri",
            "status",
            "bytes_sent",
            "object_size",
            "total_time",
            "turn_around_time",
            "referrer",
            "user_agent",
            "cipher_suite",
            "host_header",
            "datafile_id",
            "datafile_source",
            "datafile_created",
            "datafile_user_id",
            "datafile_basename",
            "datafile_download_url",
        ]
    timestamp = str(datetime.now(timezone.utc).isoformat())
    accesslogs = get_all_results(accesslog_api_url)

    # Group log events by project and serialize to lists
    log_events = {}
    for access_log in accesslogs:
        try:
            if access_log["datafile"]:
                project = access_log["datafile"]["source"]
            else:
                continue
        except KeyError:
            # Sometimes, a log file gets deleted between an access event and log retrieval
            # In these instances, skip the log
            continue

        row = []
        for header in headers:
            if header in access_log:
                field = access_log[header]
                if access_log[header] is None:
                    field = "-"
                else:
                    field = str(access_log[header])
            elif "datafile_" in header:
                key = header[9:]
                if key in access_log["datafile"]:
                    if access_log["datafile"][key] is None:
                        field = "-"
                    else:
                        field = str(access_log["datafile"][key])
            elif "key_" in header:
                key = header[4:]
                if key in access_log["key"]:
                    if access_log["key"][key] is None:
                        field = "-"
                    else:
                        field = str(access_log["key"][key])
            else:
                field = "-"
            row.append(field.strip(","))

        if project in log_events.keys():
            log_events[project].append(row)
        else:
            log_events[project] = [row]

    # Combine lists for each project as csv files and upload
    for project, items in log_events.items():
        filename = "datalogs_{0}_{1}_{2}_{3}_{4}.csv".format(
            access_point, project, start_date, end_date, timestamp
        )

        csv = ""
        for row in items:
            if csv:
                csv = "{0}\n{1}".format(csv, ",".join(row))
            else:
                csv = ",".join(row)
        csv = "{0}\n{1}".format(",".join(headers), csv)  # Prepend the headers
        f = io.StringIO(csv)
        logger.info("Writing {0}".format(filename))
        upload_stream(
            f,
            filename,
            metadata={
                "description": "Open Humans access logs:  AWS side",
                "tags": ["logs", "access logs", "AWS access logs"],
            },
            access_token=access_token,
        )


@shared_task
def get_logs(oh_member_pk, start_date=None, end_date=None):
    """
    Celery task to retrieve the specified set of logs and save them as files
    """
    oh_member = OpenHumansMember.objects.get(pk=oh_member_pk)
    access_token = oh_member.get_access_token()
    serialize_accesslogs(
        "newdatafileaccesslog", oh_member, access_token, start_date, end_date
    )
    serialize_accesslogs(
        "awsdatafileaccesslog", oh_member, access_token, start_date, end_date
    )

    return
