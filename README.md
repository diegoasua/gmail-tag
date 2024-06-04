# Automatically tag Gmail emails

## Usage

- Add a `.env` file with an `OPENAI_API_KEY`
- In GCP create a Gmail API service OAuth 2.0 credentials and add the file as `credentials.json` into the base repo

NB: Remember to whitelist your domain for `uri redirect` to work correctly. If running locally add redirect from `http://localhost:8080`


### Optional

- Edit categories in `main.py` under `TAGS`
- Edit `MAX_RESULTS` for the number of emails to pull

