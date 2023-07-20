import os
import json


class ConnectionSettings:
    @staticmethod
    def load():
        try:
            with open("settings.json", "r") as json_file:
                settings = json.load(json_file)
                databases = [setting["dbname"] for setting in settings["setting"]]
                return databases
        except FileNotFoundError:
            return []

    @staticmethod
    def save(new_settings):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as json_file:
                    existing_settings = json.load(json_file)
                    for setting in existing_settings["setting"]:
                        if setting["dbname"] == new_settings["setting"][0]["dbname"] and setting["port"] == \
                                new_settings["setting"][0]["port"]:
                            setting["actual"] = True
                            break
                    else:
                        existing_settings["setting"].append(new_settings["setting"][0])
            else:
                existing_settings = new_settings

            with open("settings.json", "w") as json_file:
                json.dump(existing_settings, json_file, indent=4)
            return True
        except Exception as e:
            # Handle the error and return False to indicate settings save failure
            # You may also add logging for the error
            return False
