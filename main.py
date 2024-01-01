from src import utils

# Initiate

# You must have your twitter api CONSUMER_KEY and CONSUMER_SECRET in an .env file
# If you have your twitter api ACCESS_TOKEN and ACCESS_TOKEN_SECRET in the .env file
# The session will be created with them
# If you don't have them, we will create them for you

# Initiate the session
# We initiate the google sheets module
sheets = utils.init_sheets()
oauth, open_ai_key, short_url_key, category, rss_list, prompt = utils.initiate_session(
    sheets
)

# Make the request given a RSS feed
url = rss_list[0]
response = utils.make_request(oauth, url, open_ai_key, short_url_key, category, prompt)

tweet_url = response.get("data").get("text").split(" ")[-1]
