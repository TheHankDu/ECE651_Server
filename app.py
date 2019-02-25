from flask import Flask
from flask_cors import CORS

app = Flask("dingziku")
app.secret_key = 'qiangulubuzhuanhouguluzhuan'
CORS(app)
