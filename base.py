from flask import Flask, jsonify, request
import psycopg2


DATABASE_URL = ""
app = Flask(__name__)







if __name__ == '__main__':
    app.run(debug=True)