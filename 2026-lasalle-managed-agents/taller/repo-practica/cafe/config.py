import os

# Llave para firmar las cookies de sesión del panel.
SECRET_KEY = os.environ.get("CAFE_SECRET_KEY", "cafe-origen-2024-cambiar")
DEBUG = True
TRANSPORTADORA_URL = "https://api.transportadora.example.com/v1/guias"
