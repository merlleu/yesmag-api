from yesmag import YesMagAPI
import time
import datetime
import random
import getpass
import json
EMAIL = input("Email: ")
PASSWORD = getpass.getpass("Password: ")

api = YesMagAPI(EMAIL, PASSWORD)
usr = api.get_user()
print("Logged-in as {} ({})".format(usr['email'], usr['id']))

NUM_ARTICLES = int(input("Nombre d'articles à marquer comme lus: "))
# NUM_ARTICLES = 1
SECONDES_PASSEES = random.randint(100, 400)*NUM_ARTICLES # nombre de secondes à ajouter aux stats
ACCURACY = 0.92


def ts(t):
        return datetime.datetime.fromtimestamp(t/1000 - 3600).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"

# timer
def process_timer():
    time_left = SECONDES_PASSEES
    timer_range = 151

    while time_left > 0:
        # get a random start date between 1 and 25 days ago
        start_time = int(time.time()) - random.randint(24, 24*25) * 60 * 60
        time_bucket_left = random.randint(3600, 3*3600) #  a bit more than 2 hours, max period to avoid detection

        session_duration = min(time_left, time_bucket_left)
        session_duration = datetime.timedelta(seconds=session_duration)

        print("SESSION: {}".format(session_duration))

        while time_left > 0 and time_bucket_left > 0:
            t = round((start_time + time_bucket_left + random.random())*1000)

            api.post_bag(
                {"type": "userSession", "json": {"id": t, "date": ts(t), "time": 151}}
            )
            print("SET PRESENCE FOR {}".format(ts(t)))
            time_bucket_left -= timer_range
            time_left -= timer_range
            # time.sleep(1)

# articles
def process_articles():
    articles = api.get_articles()
    articles_lus = {_['json']['articleId']: 1 for _ in api.get_bags()['hydra:member'] if _['type'] == 'articleRead'}

    articles_non_lus = [
        a for a in articles if a['id'] not in articles_lus and a.get('quizz')
    ]

    

    for i in range(NUM_ARTICLES):
        article = articles_non_lus.pop()

        tm = round((time.time() - random.randint(3600, 3600*24*25))*1000)
        tm_start = tm - random.randint(100_000, 400_000)
        Q = api.get_quizz(article['id'])
        if not Q:
            print("NO QUIZZ FOR ARTICLE {} - {} AT {}".format(article['id'], article['title'], ts(tm_start)))
            continue
        quizz = [_['correct'] for _ in Q]
        a = api.get_article(article['id']).split("\n")
        lines = len([_ for _ in a if len(_) > 3 and not _.startswith('SOUSTITRE')]) + 1

        api.post_bag({
            "type":"articleRead",
            "json":{"articleId":article['id'],"partial":False,"date":ts(tm_start),"numberLines":lines,"dateFinished":ts(tm)}
        })

        r = [ (_-1 if random.random() < ACCURACY else -1) for _ in quizz]

        api.post_bag({
            "type":"quizz",
            "json":{
                "id":"quizz{}".format(article['id']),
                "points": len([1 for i in r if i != -1]),
                "answers": [(_ if _ != -1 else 0) for _ in r],
                "correctAnswers":[ _ for _ in quizz],
                "lastModified":ts(tm),
                "maxPoints":len(quizz)
            }
        })

        print("READ ARTICLE {} - {} AT {}".format(article['id'], article['title'], ts(tm_start)))
        # time.sleep(1)

def update_read_stats():
    stats = [_ for _ in api.get_bags()['hydra:member'] if _['type'] == 'quizz']
    for s in stats:
        j = s['json']
        print(s)
        r = [ (_-1 if random.random() < ACCURACY else -1) for _ in j['correctAnswers']]
        
        j['answers'] = [(_ if _ != -1 else 0) for _ in r]
        j['points'] = len([1 for i in range(len(r)) if r[i] != -1])
        j['lastModified'] = j['lastModified'][:-2] + str(random.randint(0, 9)) +  "Z"
        print(s)
        api.put_bag(s['id'], {"json": j})

def remove_future_stats():
    for s in api.get_bags()['hydra:member']:
        j = s['json']
        if isinstance(j, dict) and( j.get('date','').startswith('2501') or j.get('lastModified','').startswith('2501')):
            print("UPDATE {}".format(json.dumps(j)))
            if 'date' in j:
                j['date'] = j['date'].replace('2501', '2022')
            if 'dateFinished' in j:
                j['dateFinished'] = j['dateFinished'].replace('2501', '2022')
            if 'lastModified' in j:
                j['lastModified'] = j['lastModified'].replace('2501', '2022')
            print(api.put_bag(s['id'], s))
    
    # remove previous stats...
    stats = api.get_bags()['hydra:member']
    i = 0
    for bag in stats:
        if bag['type'] == 'userStats':
            j = bag['json']
            j = [ _ for _ in j if 'date' not in _ or not _['date'].startswith('2501') ]
            print(j)
            api.put_bag(bag['id'], {"json": j})
            i += 1
    print(i)
    
        
    
if __name__ == "__main__":
    while True:
        print("1 - Marquer des articles comme lus")
        print("2 - Simuler un temps de lecture")
        print("3 - Mettre à jour les réponses de QCM pour atteindre l'objectif d'accuracy.")
        print("4 - Supprimer les stats futures")
        print("5 - Quitter")
        choice = input("Choix: ")
        if choice == '1':
            process_articles()
        elif choice == '2':
            process_timer()
        elif choice == '3':
            update_read_stats()
        elif choice == '4':
            remove_future_stats()
        elif choice == '5':
            break
        else:
            print("Choix invalide")

        print("")