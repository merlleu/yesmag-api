import requests
from .oauth import *

class YesMagAPI:
    auth = None
    session = requests.Session()
    def __init__(self, email: str, password: str, save_file: str = None) -> None:
        self.oauth = YesMagOAuth(self.session, email, password, save_file=save_file)
    
    # makes an authenticated request to the API
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = self.oauth.bearer()

        r = self.session.request(method, url, **kwargs)
        if r.status_code == 401:
            self.oauth._login()
            r = self.session.request(method, url, **kwargs)
        return r


    def get_user(self, user_id: int = None):
        if user_id is None:
            user_id = self.oauth.user()
        return self._request("GET", f"https://api.yesmag.fr/api/users/{user_id}").json()
    
    def get_bags(self):
        return self._request("GET", "https://api.yesmag.fr/api/user/bags").json()
    
    def put_bag(self, bag_id: int, data: dict):
        return self._request("PUT", f"https://api.yesmag.fr/api/user/bags/{bag_id}", json=data).json()
    
    def post_bag(self, data: dict):
        return self._request("POST", "https://api.yesmag.fr/api/user/bags", json=data).json()
    
    def get_articles(self):
        return self.session.get("https://yesmag.fr/webapp/data/articles/articles.json?cachebust={}".format(int(time.time()))).json()
    
    def get_article(self, article_id: int):
        return self.session.get("https://yesmag.fr/webapp/data/articles/article-{}.csv".format(article_id)).text

    def get_quizz(self, quizz_id: int):
        return self.session.get("https://yesmag.fr/webapp/data/quizz/{}.json?cachebust={}".format(quizz_id, int(time.time()))).json()
    
