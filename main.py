from app import flask_app, gui_app, config

if __name__ == '__main__':
    if bool(int(config["FLASK"]["app"])):
        gui_app.run()
    else:
        flask_app.run(port=int(config["FLASK"]["port"]))

