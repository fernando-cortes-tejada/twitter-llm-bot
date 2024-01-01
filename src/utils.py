# import asyncio
import requests
from bs4 import BeautifulSoup
import feedparser
import os
import re
import tweepy
from requests_oauthlib import OAuth1Session
from src.langchain import utils as langchain
from src.sheets import main as sheets
from src.drive import main as drive
from src.entities import SHEETS_URL


###### LOAD SHEETS DATA #######
def init_sheets() -> list[list[str]]:
    sheets.get_service_sheets()
    sheets_id = drive.drive_folder_url_to_id(SHEETS_URL)
    sheets_db = sheets.gsheets_read(sheets_id, "settings!A:K")
    sheets_values = [v[2:] for v in sheets_db["values"][1:]]
    return sheets_values


###### INITIATE SESSION #######
def initiate_session(
    sheets_values: list[list[str]],
) -> tuple[OAuth1Session, str, str, list[str], str]:
    (
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
        open_ai_key,
        short_url_key,
        category,
        rss_list,
        prompt,
    ) = sheets_values[1]

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )
    rss_list = rss_list.split(",")
    return oauth, open_ai_key, short_url_key, category, rss_list, prompt


def generate_autorizathion(consumer_key: str, consumer_secret: str) -> tuple[str, str]:
    # Request token with write permissions
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print(
            "There may have been an issue with the consumer_key or consumer_secret you entered."
        )

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    return access_token, access_token_secret


###### MAKE REQUEST #######


# Initiate tweepy
def initiate_tweepy(oauth: OAuth1Session) -> tweepy.API:
    tweepy_auth = tweepy.OAuth1UserHandler(
        consumer_key=oauth._client.client.client_key,
        consumer_secret=oauth._client.client.client_secret,
        access_token=oauth.token.get("oauth_token"),
        access_token_secret=oauth.token.get("oauth_token_secret"),
    )
    return tweepy.API(tweepy_auth)


# Upload media (image or video)
def get_media_payload(oauth: OAuth1Session, url: str) -> dict:
    download_media(url)
    tweepy_api = initiate_tweepy(oauth)
    file = [file for file in os.listdir() if file.split(".")[0] == "media"]
    text = str(tweepy_api.simple_upload(file[0]))
    media_id = re.search("media_id=(.+?),", text).group(1)
    payload = {"media": {"media_ids": ["{}".format(media_id)]}}
    os.remove(file[0])
    return payload


def get_text_payload(url: str, open_ai_key: str, prompt: str) -> dict:
    txt = langchain.docs_answering(url, open_ai_key, prompt)
    return {"text": txt.replace("[URL]", url).replace('"', "")}


def get_post_history() -> dict:
    return ""


def get_first_not_posted() -> dict:
    return False


def download_media(url: str) -> None:
    extension = url.split(".")[-1]
    media_bytes = requests.get(url).content
    with open(f"media.{extension}", "wb") as handler:
        handler.write(media_bytes)


def get_entries(url: str) -> list[dict]:
    entries = feedparser.parse(url).get("entries")
    lst = []
    for entry in entries:
        soup = BeautifulSoup(entry.get("content")[0].get("value"), "html.parser")
        img_url = soup.find("img").get("src")
        entry_url = soup.find("a").get("href")
        if img_url and entry_url:
            lst.append({"img_url": img_url, "entry_url": entry_url})
    return lst


def make_request(
    oauth: OAuth1Session,
    url: str,
    open_ai_key: str,
    short_url_key: str,
    category: str,
    prompt: str,
) -> dict:
    entries = get_entries(url)
    if not entries:
        print("No entries with complete information found")
        return {}

    # post_history = get_post_history()
    # entry = get_first_not_posted(entries, post_history)
    entry = entries[0]

    # Shorten the url
    # short_url = shorten_url(entry.get("entry_url"), short_url_key)

    # Get the payload in parallel
    media_payload = get_media_payload(oauth, entry.get("img_url"))
    text_payload = get_text_payload(entry.get("entry_url"), open_ai_key, prompt)
    # media_task = asyncio.create_task(get_media_payload(oauth, entry.get("img_url")))
    # text_task = asyncio.create_task(get_text_payload(entry.get("entry_url")))

    # media_payload, text_payload = await media_task, await text_task
    payload = text_payload | media_payload

    # Making the request
    response = oauth.post("https://api.twitter.com/2/tweets", json=payload)

    return response.json()


def shorten_url(url: str, api_key: str) -> str:
    headers = {
        "authorization": api_key,
        "content-type": "application/json",
    }
    body = {"domain": "b2zi.short.gy", "originalURL": url}
    res = requests.post("https://api.short.io/links", json=body, headers=headers)
    return res.json().get("shortURL")
