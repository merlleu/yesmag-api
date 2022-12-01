import json
import requests
import time
import os
import base64

class YesMagOAuth:
    def __init__(self, session: requests.Session, email: str, password: str, save_file: str = None) -> None:
        self.session = session
        self.email = email
        self.password = password
        self.token = None
        self.token_exp = 0
        self.save_file = save_file
        self._user_id = None
        self._load()

    def _login(self) -> None:
        # Login to YesMag
        # POST https://api.yesmag.fr/api/login_check
        # {
        #   "_username": "string",
        #   "_password": "string"
        # }
        #
        # Response:
        # {
        #     "token": "<TOKEN>",
        #     "refresh_token": "<TOKEN>",
        #     "@id": "\/api\/users\/123456",
        #     "id": 123456,
        #     "email": "mail@example.org"
        # }

        r = self.session.post(
            "https://api.yesmag.fr/api/login_check",
            data={
                "_username": self.email,
                "_password": self.password
            }
        )

        if r.status_code != 200:
            raise Exception("Login failed")
        else:
            j = r.json()
            self.token = j["token"]
            self._user_id = j["id"]
            self.token_exp = _get_jwt_payload(self.token)["exp"]
            self._save()

    # save oauth data to file

    def _save(self) -> None:
        if self.save_file is None:
            return
        with open(self.save_file, "w") as f:
            f.write(json.dumps({
                "token": self.token,
                "token_exp": self.token_exp,
                "_user_id": self._user_id
            }))

    # load oauth data from file
    def _load(self) -> bool:
        if self.save_file is None or not os.path.exists(self.save_file):
            return False
        with open(self.save_file, "r") as f:
            data = json.loads(f.read())
            self.token = data["token"]
            self.token_exp = data["token_exp"]
            self._user_id = data["_user_id"]
        return True

    def bearer(self) -> str:
        if self.token_exp < time.time():
            self._login()

        return "Bearer " + self.token

    def user(self) -> int:
        if self.token_exp < time.time():
            self._login()

        return self._user_id

# unsafe, but we trust the token
def _get_jwt_payload(token: str) -> dict:
    # get the 2nd part of the token (payload)
    # and decode it from base64 & parse it as json
    part = token.split(".")[1]
    return json.loads(base64.b64decode(part + "=" * (-len(part) % 4)))