import os
import subprocess
import zipfile
from base64 import b64decode
from distutils.version import LooseVersion
from pathlib import Path

import requests

from settings import ConnectionSettings
from utility_function import handle_errors

nameApp = "PgSSR"

class Updater:
    def __init__(self):
        self.username = None
        self.token = None
        self.repo = None
        self.tmp_folder = os.path.join(os.environ['TMP'], "tmp_update_folder")
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
            decoded_content = b64decode(file_content).decode("utf-8")
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
                extract_path = os.path.join(output_dir, self.repo)
                zip_ref.extractall(extract_path)

            os.remove(archive_path)
            print(f"Репозиторий {self.repo} был успешно загружен и извлечен в {extract_path}")
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
        remote_version = remote_version.strip()
        self.local_version = self.local_version.strip()
        is_update_available = LooseVersion(remote_version) > LooseVersion(self.local_version)
        if is_update_available:
            return is_update_available, remote_version
        else:
            return is_update_available, self.local_version

    @handle_errors(log_file="update.log", text='get_download_link')
    def get_download_link(self):
        releases_url = f"https://api.github.com/repos/{self.username}/{self.repo}/releases"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(releases_url, headers=headers)
        releases = response.json()

        if releases:
            latest_release = releases[0]
            latest_version = latest_release["tag_name"]
            base_url = f"https://github.com/{self.username}/{self.repo}/releases/download"
            file_name = f"{nameApp}.exe"
            url_to_download = f"{base_url}/{latest_version}/{file_name}"
            return url_to_download
        else:
            return None

    @handle_errors(log_file="update.log", text='run_update')
    def run_update(self):
        self.download_and_extract_repo_archive("zip", self.tmp_folder)
        extract_path = os.path.join(self.tmp_folder, self.repo)
        os.chdir(os.path.join(extract_path, f"{self.repo}-main"))
        subprocess.run(["python", "update.py", "build"], stdout=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW)
