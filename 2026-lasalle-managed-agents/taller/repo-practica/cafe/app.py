"""API de Café Origen: pedidos, facturas y rastreo de envíos."""
from pathlib import Path

import requests
from flask import Flask, abort, jsonify, request, send_file

from cafe import config, db

FACTURAS = Path(__file__).resolve().parents[1] / "facturas"


def crear_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    con = db.conectar()

    @app.get("/salud")
    def salud():
        return {"ok": True}

    @app.get("/pedidos")
    def pedidos():
        correo = request.args.get("correo", "")
        if not correo:
            abort(400)
        return jsonify(db.pedidos_de(con, correo))

    @app.get("/facturas/<path:nombre>")
    def factura(nombre: str):
        ruta = FACTURAS / nombre
        if not ruta.exists():
            abort(404)
        return send_file(ruta)

    @app.get("/rastreo/<guia>")
    def rastreo(guia: str):
        respuesta = requests.get(f"{config.TRANSPORTADORA_URL}/{guia}", timeout=5)
        return respuesta.json()

    return app


if __name__ == "__main__":
    crear_app().run(debug=config.DEBUG)
