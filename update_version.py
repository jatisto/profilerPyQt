import os
import subprocess
import urllib.request
import shutil
from distutils.version import LooseVersion
from pathlib import Path


def get_local_version():
    version_file = Path("version.txt")
    if version_file.is_file():
        with open(version_file, "r") as f:
            return f.read().strip()
    return "0.0"


def get_remote_version():
    url = "https://raw.githubusercontent.com/jatisto/profilerPyQt/main/version.txt"
    with urllib.request.urlopen(url) as response:
        return response.read().decode().strip()


def download_and_extract_repository(download_path):
    repo_url = "https://github.com/jatisto/profilerPyQt/archive/main.zip"
    zip_path = os.path.join(download_path, "main.zip")
    urllib.request.urlretrieve(repo_url, zip_path)
    shutil.unpack_archive(zip_path, download_path)
    os.remove(zip_path)


def update():
    local_version = get_local_version()
    remote_version = get_remote_version()

    if LooseVersion(remote_version) > LooseVersion(local_version):
        print("Доступно обновление!")

        response = input("Вы хотите обновить приложение? (yes/no): ")
        if response.lower() == "yes":
            tmp_folder = "tmp_update_folder"
            os.makedirs(tmp_folder, exist_ok=True)
            download_and_extract_repository(tmp_folder)

            os.chdir(os.path.join(tmp_folder, "profilerPyQt-main"))
            subprocess.run(["python", "setup.py", "build"])
            dist_folder = os.path.join("dist")
            msi_files = [file for file in os.listdir(dist_folder) if file.endswith(".msi")]

            if msi_files:
                msi_path = os.path.join(dist_folder, msi_files[0])
                subprocess.run(["msiexec", "/i", msi_path])
            else:
                print("Файл установки не найден.")

            os.chdir("..")
            shutil.rmtree(tmp_folder)

            print("Обновление завершено.")
        else:
            print("Обновление отменено.")
    else:
        print("У вас уже установлена последняя версия.")
