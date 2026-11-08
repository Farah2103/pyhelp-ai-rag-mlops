import argparse,json
from api.main import get_assistant
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("question");a=p.parse_args()
    print(json.dumps(get_assistant().ask(a.question),ensure_ascii=False,indent=2))
