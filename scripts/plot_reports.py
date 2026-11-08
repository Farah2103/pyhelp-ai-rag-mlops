from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.common import ROOT,read_json

def plots():
    folder=ROOT/"reports/figures";folder.mkdir(exist_ok=True)
    c=read_json(ROOT/"reports/comparison.json")
    fig,ax=plt.subplots(figsize=(8,4.4))
    xx=range(2);ax.bar([x-.15 for x in xx],[100*r["test"]["recall_fr"] for r in c],width=.3,label="Français",color="#15776e")
    ax.bar([x+.15 for x in xx],[100*r["test"]["recall_en"] for r in c],width=.3,label="English",color="#246292")
    ax.set_xticks(list(xx),["A · 400/80 · k=3","B · 800/120 · k=5"]);ax.set_ylim(0,100)
    ax.set_ylabel("Rappel des groupes de preuves (%)")
    ax.set_title("PyHelp AI — retrieval réel sur le jeu de test")
    ax.legend();ax.spines[["top","right"]].set_visible(False);fig.tight_layout();fig.savefig(folder/"retrieval_languages.png",dpi=160);plt.close(fig)
    p=ROOT/"monitoring/demo_requests.jsonl"
    if p.exists():
        rows=[json.loads(x) for x in p.read_text().splitlines() if x];rows=[r for r in rows if r["path"]=="/ask"]
        fig,ax=plt.subplots(figsize=(8,4.4));ax.bar(range(len(rows)),[r["latency_ms"]/1000 for r in rows],color=["#15776e" if r["http_status"]==200 else "#c07326" for r in rows])
        ax.set_xticks(range(len(rows)),[str(r["http_status"])+" · "+r["status"] for r in rows],rotation=10);ax.set_ylabel("Latence observée (s)");ax.set_title("Démonstration HTTP — premier appel avec chargement local")
        ax.spines[["top","right"]].set_visible(False);fig.tight_layout();fig.savefig(folder/"monitoring_demo.png",dpi=160);plt.close(fig)
    print("Figures written",folder)
if __name__=="__main__":plots()
