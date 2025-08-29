from flask import Flask, request, redirect, render_template, jsonify
from datetime import datetime
import threading

app = Flask(__name__)

links_rastreaveis = {}
lock = threading.Lock()
cliques = []

def salvar_cliques_txt():
    with open("cliques.txt", "w", encoding="utf-8") as f:
        for c in cliques:
            f.write(f"{c['ts']} - IP: {c['ip']} - UA: {c['ua']} - Link: {c['link']}\n")

@app.route("/", methods=["GET", "POST"])
def home():
    link_compartilhavel = ""
    if request.method == "POST":
        link_real = request.form.get("link_real")
        chave_custom = request.form.get("chave_custom").strip()
        if not chave_custom:
            return "Você precisa digitar um nome para o link.", 400

        with lock:
            if chave_custom in links_rastreaveis:
                return "Essa chave já existe. Escolha outra.", 400
            links_rastreaveis[chave_custom] = {"real": link_real, "cliques": []}

            # CORREÇÃO: link completo com domínio público
            link_compartilhavel = f"{request.host_url}r/{chave_custom}"

    return render_template("index.html", link_compartilhavel=link_compartilhavel, cliques=cliques)

@app.route("/r/<chave>")
def rastrear(chave):
    if chave not in links_rastreaveis:
        return "Link inválido.", 404
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with lock:
        clique = {"ts": ts, "ip": ip, "ua": ua, "link": links_rastreaveis[chave]["real"]}
        links_rastreaveis[chave]["cliques"].append(clique)
        cliques.append(clique)
        salvar_cliques_txt()

    return redirect(links_rastreaveis[chave]["real"])

@app.route("/cliques")
def cliques_json():
    with lock:
        return jsonify(cliques)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
