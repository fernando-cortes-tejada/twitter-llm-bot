import json
import requests
import urllib.parse
from src.drive import utils
from src.drive import entities


# we get the id from the url
def drive_folder_url_to_id(url: str) -> str:
    url_split = url.split("/")
    if "edit" in url_split[-1]:
        return url_split[-2]
    else:
        return url_split[-1]


def get_files_in_folder(folder_id: str):
    service = utils.get_service_drive()
    response = (
        service.files().list(q=f"'{folder_id}' in parents", spaces="drive").execute()
    )
    return response.get("files")


def copy_file(name: str, template_id: str, parent_id: str):
    utils.get_service_drive()
    creds = json.load(open(entities.GCP_TOKEN_LOCATION))
    url = f"https://www.googleapis.com/drive/v3/files/{template_id}/copy?key={creds.get('client_secret')}"
    headers = {
        "Authorization": f"Bearer {creds.get('token')}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {"name": name}
    if parent_id != "":
        data["parents"] = [parent_id]
    r = requests.post(url=url, headers=headers, json=data)
    file_id = json.loads(r.__dict__.get("_content")).get("id")

    return file_id


def modify_permission(file_id: str, email: str, message: str = ""):
    utils.get_service_drive()
    creds = json.load(open(entities.GCP_TOKEN_LOCATION))
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?key={creds.get('client_secret')}"
    if message:
        url += f"&emailMessage={urllib.parse.quote(message)}"
    headers = {
        "Authorization": f"Bearer {creds.get('token')}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {"role": "reader", "type": "user", "emailAddress": email}
    r = requests.post(url=url, headers=headers, json=data)
    return r.__dict__.get("_content")
