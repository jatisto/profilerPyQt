import logging
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
    def load_all_settings():
        try:
            with open("settings.json", "r") as json_file:
                return json.load(json_file)["setting"]
        except FileNotFoundError:
            return []

    @staticmethod
    def load_json(name_file, root_element):
        try:
            with open(name_file, "r") as json_file:
                return json.load(json_file)[root_element]
        except FileNotFoundError:
            return []

    @staticmethod
    def save(new_settings):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as json_file:
                    existing_settings = json.load(json_file)
                    found_matching = False

                    for setting in existing_settings["setting"]:
                        if (setting["dbname"] == new_settings["setting"][0]["dbname"] and
                                setting["port"] == new_settings["setting"][0]["port"] and
                                setting["host"] == new_settings["setting"][0]["host"]):
                            setting["actual"] = True
                            found_matching = True
                        else:
                            setting["actual"] = False  # Сбросить флаг actual для остальных записей

                    if not found_matching:
                        existing_settings["setting"].append(new_settings["setting"][0])
            else:
                existing_settings = new_settings

            with open("settings.json", "w") as json_file:
                json.dump(existing_settings, json_file, indent=4)
            return True
        except Exception as e:
            logging.Formatter(f"{e}")
            return False
