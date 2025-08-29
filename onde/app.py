from flask import Flask, request, redirect, jsonify, render_template
from datetime import datetime
import threading
import os

app = Flask(__name__)

lock = threading.Lock()
links_rastreaveis = {}
cliques = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "error": "JSON inválido ou vazio"}), 400

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

    raw_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = raw_ip.split(",")[0].strip()
    ua = request.headers.get("User-Agent")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    clique = {"ts": ts, "chave": chave, "ip": ip, "ua": ua, "link": links_rastreaveis[chave]["real"]}

    with lock:
        links_rastreaveis[chave]["cliques"].append(clique)
        cliques.append(clique)

    print(f"[DEBUG] Clique: Chave={chave}, IP={ip}, UA={ua}, Hora={ts}")
    return redirect(links_rastreaveis[chave]["real"])

@app.route("/cliques")
def listar_cliques():
    with lock:
        return jsonify(cliques)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
