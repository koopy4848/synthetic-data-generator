from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/documentation')
def documentation():
    return render_template('home.html')


@app.route('/generator_one')
def generator_one():
    return render_template('generate.html')


@app.route('/generator_two')
def generator_two():
    return render_template('generate.html')


@app.route('/generator_three')
def generator_three():
    return render_template('generate.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
