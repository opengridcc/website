from flask_app import app, env

if __name__ == "__main__":
    if env == 'dev':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        app.run(debug=False, host='0.0.0.0', port=5000)
