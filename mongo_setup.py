import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém a string de conexão MongoDB da variável de ambiente MONGODB_URI
mongodb_uri = os.getenv("MONGO_URI")
mongodb_collection = os.getenv("MONGO_DB")

# Conecta-se ao MongoDB
client = MongoClient(mongodb_uri)
db = client[mongodb_collection]