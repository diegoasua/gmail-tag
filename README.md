# Automatically tag Gmail emails

## Usage

- Add a `.env` file with an `OPENAI_API_KEY`
- In GCP create a Gmail API service and put the `credentials.json` file into the repo

NB: Remember to whitelist your domain for `uri redirect` to work correctly


### Optional

- Edit categories in `main.py` under `TAGS`
- Edit `MAX_RESULTS` for the number of emails to pull
