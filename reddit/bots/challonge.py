import json
import logging
from datetime import datetime
from urllib.request import Request, HTTPBasicAuthHandler, build_opener

import dotenv
import pytz
import telegram

from reddit.bots.database import set_stats, bulk_update, filter_by_ids
from reddit.settings import LOGGING_FORMAT

config = dotenv.dotenv_values()

bot = telegram.Bot(token=config["CHALLONGE_BOT_TOKEN"])

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def convert_to_timezone(datetime_string, tz="UTC"):
    if datetime_string:
        datetime_string = datetime_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(datetime_string).astimezone(pytz.timezone(tz))
        if tz == "UTC":
            return dt.isoformat()
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class Client:
    def __init__(self, tournament_id):
        params = "include_matches=1&include_participants=1"
        tournament_url = config["CHALLONGE_URL"].format(tournament_id)
        self.tournament_data = None
        self.tournament_id = tournament_id
        self.url = f"{tournament_url}?{params}"

    def _get_related(self, field):
        suffix = "s" if field == "participant" else "es"
        return {m[field]['id']: m[field] for m in self.tournament_data[f"{field}{suffix}"]}

    @property
    def matches(self):
        return self._get_related("match")

    @property
    def participants(self):
        return self._get_related("participant")

    def fetch(self):
        req = Request(self.url)
        req.get_method = lambda: "GET"
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm="Application",
            uri=req.get_full_url(),
            user=config["CHALLONGE_USERNAME"],
            passwd=config["CHALLONGE_API_KEY"]
        )
        opener = build_opener(auth_handler)
        with opener.open(req) as response:
            self.tournament_data = json.loads(response.read())["tournament"]
            return self.tournament_data

    def get_player_name(self, player_id):
        return self.participants[player_id]['name'] if player_id else "?"

    def get_players_from_match_id(self, match_id):
        match_data = self.matches[match_id]
        player1 = self.get_player_name(match_data['player1_id'])
        player2 = self.get_player_name(match_data['player2_id'])
        return f"{player1} vs {player2}"

    def get_update_verbose(self, update_field, update_value):
        field_verbose = update_field.replace('_', " ").capitalize()
        if not update_value:
            return f"Cleared: {field_verbose}"
        if update_field == "scores_csv":
            return f"Score: {update_value.replace('-', ':')}"
        if update_field in ["underway_at", "started_at", "completed_at"]:
            verbose = convert_to_timezone(update_value, "Europe/Bucharest")
            return f"{field_verbose}: {verbose} (± 5m)"
        if update_field in ["loser_id", "winner_id", "player1_id", "player2_id"]:
            field = update_field.split("_")[0].title()
            emoji = "💪" if update_field == "winner_id" else ""
            return f"{field}: {self.get_player_name(update_value)}{emoji}"
        return f"{update_field.title()}: {update_value}"

    def parse_update(self, update):
        match_id = update._filter['id']
        match_name = f"{self.get_players_from_match_id(match_id)} [Round {self.matches[match_id]['round']}]"
        match_title = f"<b>{match_name}</b>"
        match_updates = {
            k: v for k, v in update._doc["$set"].items() if k != "updated_at"
        }
        match_updates = [f' {self.get_update_verbose(*item)}' for item in match_updates.items()]
        match_updates = '\n'.join(sorted(match_updates))
        return f"{match_title}\n{match_updates}"

    def parse_updates(self, items):
        items = "\n\n".join([self.parse_update(u) for u in items])
        return (
            "<b>Hi, these are the new updates:</b>"
            f"\n\n{items}"
            f"\n\n<a href='https://challonge.com/{self.tournament_id}'>"
            f"Tournament page"
            f"</a>"
        )


def check():
    client = Client(tournament_id=config["CHALLONGE_DATABASE_NAME"])
    client.fetch()

    db_matches = {m['id']: m for m in filter_by_ids(list(client.matches))}

    updates = []
    for _id, match in client.matches.items():
        match["created_at"] = convert_to_timezone(match["created_at"])
        match["updated_at"] = convert_to_timezone(match["updated_at"])
        match["underway_at"] = convert_to_timezone(match["underway_at"])
        match["started_at"] = convert_to_timezone(match["started_at"])
        match["completed_at"] = convert_to_timezone(match["completed_at"])

        db_match = db_matches.get(match['id'])
        if db_match and match.items() <= db_match.items():
            continue
        db_match = db_match or {}
        updates.append(set_stats(dict(match.items() - db_match.items()), commit=False, id=match["id"]))

    if updates:
        results = bulk_update(updates).bulk_api_result
        bot.send_message(
            chat_id=config["CHALLONGE_CHAT_ID"],
            text=client.parse_updates(updates),
            parse_mode=telegram.ParseMode.HTML
        )
        logger.debug(results)
    else:
        logger.info(f"No updates")

    logger.info("Done")


if __name__ == "__main__":
    check()