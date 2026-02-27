from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # Kau boleh letak logik Python kat sini nanti
    data = {
        "title": "Faridexholic Will Come back :D",
        "status": "Online",
        "version": "Mess with the best, die like the rest"
    }
    return render_template('index.html', data=data)

if __name__ == '__main__':

    app.run(debug=True)


