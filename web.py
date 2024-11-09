from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('index.html')

@app.route('/faucet')
def faucet():
   return render_template('testnet.html')

if __name__ == '__main__':
   app.run()