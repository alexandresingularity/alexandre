from flask import Flask, request, redirect, render_template, jsonify
from datetime import datetime
import threading

app = Flask(__name__)

links_rastreaveis = {}   # { "chave": { "real": "url real", "cliques": [] } }
cliques = []             # lista global de todos os cliques
lock = threading.Lock()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create():
    try:
        data = request.get_json(force=True)  # força leitura do JSON
    except Exception as e:
        return jsonify({"ok": False, "error": f"JSON inválido: {e}"}), 400

    link_real = (data.get("link_real") or "").strip()
    chave = (data.get("chave") or "").strip()

    if not link_real or not chave:
        return jsonify({"ok": False, "error": "link_real e chave são obrigatórios"}), 400

    with lock:
        if chave in links_rastreaveis:
            return jsonify({"ok": False, "error": "Chave já existe"}), 400
        links_rastreaveis[chave] = {"real": link_real, "cliques": []}

    return jsonify({"ok": True, "short": f"/r/{chave}"})

@app.route("/r/<chave>")
def redirecionar(chave):
    if chave not in links_rastreaveis:
        return "Link inválido", 404

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    clique = {"ts": ts, "chave": chave, "ip": ip, "ua": ua, "link": links_rastreaveis[chave]["real"]}

    with lock:
        links_rastreaveis[chave]["cliques"].append(clique)
        cliques.append(clique)

    return redirect(links_rastreaveis[chave]["real"])

@app.route("/cliques")
def listar_cliques():
    with lock:
        return jsonify(cliques)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
