import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from src.sheets import entities


# create the sheets service and regenerate the token if needed
def get_service_sheets():
    creds = None
    if os.path.exists(entities.GCP_TOKEN_LOCATION):
        creds = Credentials.from_authorized_user_file(
            entities.GCP_TOKEN_LOCATION, entities.SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                entities.GCP_CRED_LOCATION, entities.SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(entities.GCP_TOKEN_LOCATION, "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def gsheets_write(values, spreadsheet_id, range_):
    service = get_service_sheets()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )
    return result


def gsheets_append(values, spreadsheet_id, range_):
    service = get_service_sheets()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )
    return result


def gsheets_read(spreadsheet_id, range_):
    service = get_service_sheets()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_)
        .execute()
    )
    return result
