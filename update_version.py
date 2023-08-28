import base64
import os
import shutil
import subprocess
import zipfile
from distutils.version import LooseVersion
from pathlib import Path

import psutil
import requests

from settings import ConnectionSettings
from utility_function import handle_errors, write_log


class Updater:
    def __init__(self):
        self.username = None
        self.token = None
        self.repo = None
        self.tmp_folder = "tmp_update_folder"
        self.file_path = "version.txt"
        self.local_version = self.get_local_version()
        self.load_auth_data_for_git()

    @staticmethod
    @handle_errors(log_file="update.log", text='get_local_version')
    def get_local_version() -> str:
        version_file = Path("version.txt")
        if version_file.is_file():
            with open(version_file, "r") as f:
                return f.read().strip()
        return "0.0.0"

    @handle_errors(log_file="update.log", text='get_remote_version')
    def get_remote_version(self) -> str:
        url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{self.file_path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        data = response.json()

        if "content" in data:
            file_content = data["content"]
            decoded_content = base64.b64decode(file_content).decode("utf-8")
            return decoded_content
        else:
            return "0.0.0"

    @handle_errors(log_file="update.log", text='download_and_extract_repo_archive')
    def download_and_extract_repo_archive(self, archive_format, output_dir):
        archive_url = f"https://github.com/{self.username}/{self.repo}/archive/refs/heads/main.{archive_format}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(archive_url, headers=headers)
        if response.status_code == 200:
            archive_path = f"{self.repo}_archive.{archive_format}"
            with open(archive_path, "wb") as file:
                file.write(response.content)

            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(output_dir)

            os.remove(archive_path)
            print(f"Репозиторий {self.repo} был успешно загружен и извлечен в {output_dir}")
        else:
            print("Не удалось загрузить архив репозитория.")

    @handle_errors(log_file="update.log", text='load_auth_data_for_git')
    def load_auth_data_for_git(self):
        data = ConnectionSettings.load_json("auth.json", "Auth")
        self.username = data["username"]
        self.token = data["token"]
        self.repo = data["repo"]

    @handle_errors(log_file="update.log", text='check_update')
    def check_update(self):
        remote_version = self.get_remote_version()

        if LooseVersion(remote_version) > LooseVersion(self.local_version):
            return True
        else:
            return False

    @handle_errors(log_file="update.log", text='run_update')
    def run_update(self):
        self.download_and_extract_repo_archive("zip", self.tmp_folder)
        os.chdir(os.path.join(self.tmp_folder, f"{self.repo}-main"))
        subprocess.run(["python", "setup.py", "bdist_msi"])
        dist_folder = os.path.join("dist")
        msi_files = [file for file in os.listdir(dist_folder) if file.endswith(".msi")]
        if msi_files:
            msi_path = os.path.join(dist_folder, msi_files[0])
            cmd = ["msiexec", "/i", msi_path]  # "/qn" означает "тихая" установка без отображения окон
            subprocess.run(cmd, check=True)
        else:
            return "Установочный файл не найден."

        return "Обновление завершено."

    @staticmethod
    @handle_errors(log_file="update.log", text='remove_program')
    def remove_program():
        install_path = os.path.join(os.environ["APPDATA"], "Local", "Programs",
                                    "PgProfilerQt5")  # Путь к установленной папке приложения

        try:
            for root, dirs, files in os.walk(install_path):
                for file in files:
                    if file not in ["settings.json", "auth.json"]:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)  # Удаление файла

                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    shutil.rmtree(dir_path)  # Удаление папки

            write_log("Программа успешно удалена, оставив settings.json и auth.json.")
        except Exception as e:
            write_log("Произошла ошибка при удалении программы:", e)
