from flask import Flask, render_template

app = Flask(__name__)

@app.route('/portal')
def portal():
    return render_template('portal.html')

if __name__ == '__main__':
    app.run(port=5000)
