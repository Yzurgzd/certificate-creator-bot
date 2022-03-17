import requests
import zipfile
import io
import shutil
import os
import sys
import subprocess
import platform
import pdfkit
import codecs
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


API_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
TOKEN = 'AQAAAABd5mqJAAe9khiCTWYyg01hgANyRYKFcdU'

headers = {'Content-Type': 'application/json',
           'Accept': 'application/json', 'Authorization': f'OAuth {TOKEN}'}


def extract_zip(href) -> None:
    res = requests.get(href)
    zip = zipfile.ZipFile(io.BytesIO(res.content))
    zip.extractall()


def get_folders() -> list:
    folders = []
    res = requests.get(f'{API_URL}?path=certificates', headers=headers)
    if res.ok:
        data = res.json()
        folders = data["_embedded"]["items"]
    return folders


def put_publish(path) -> str:
    res = requests.put(f'{API_URL}/publish?path={path}', headers=headers)
    data = res.json()
    return data["href"]


def get_publish(href) -> str:
    res = requests.get(href, headers=headers)
    data = res.json()
    return data["public_url"]


def create_folder(path) -> bool:
    res = requests.put(f'{API_URL}?path=certificates/{path}', headers=headers)
    if res.ok:
        return True
    return False


def upload_file(loadfile, savefile, replace=False) -> None:
    res = requests.get(
        f'{API_URL}/upload?path={savefile}&overwrite={replace}', headers=headers).json()
    with open(loadfile, 'rb') as f:
        try:
            requests.put(res['href'], files={'file': f})
        except KeyError:
            pass


def update_templates() -> bool:
    fullpath = os.getcwd() + "/templates"
    if os.path.exists(fullpath):
        shutil.rmtree(fullpath)
    res = requests.get(f'{API_URL}/download?path=templates', headers=headers)
    if res.ok:
        data = res.json()
        href = data["href"]
        extract_zip(href)
        return True
    return False


def render_html(template_name, subtitle, date, names) -> None:
    Path('templates/html').mkdir(parents=True, exist_ok=True)

    root = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(root, 'templates/layout')
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template(template_name)

    for name in names:
        data = {}
        data["name"] = name
        data["subtitle"] = subtitle
        data["date"] = date
        filename = os.path.join(
            root + "/templates", 'html', f'{name}.html')
        with codecs.open(filename, 'w', 'utf-8') as fh:
            fh.write(template.render(data))
        data.clear()


def to_pdf() -> None:
    if platform.system() == "Windows":
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=os.environ.get(
            'WKHTMLTOPDF_BINARY', 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'))
    else:
        os.environ['PATH'] += os.pathsep + os.path.dirname(sys.executable)
        WKHTMLTOPDF_CMD = subprocess.Popen(['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf-pack')],
                                           stdout=subprocess.PIPE).communicate()[0].strip()
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)

    Path('templates/certificate').mkdir(parents=True, exist_ok=True)
    options = {
        'enable-local-file-access': None,
        'page-size': 'A4',
        'orientation': 'Portrait',
        'zoom': '0.5',
        'margin-top': '0',
        'margin-right': '0',
        'margin-bottom': '0',
        'margin-left': '0',
        'encoding': "UTF-8",
        'no-outline': None,
    }
    for filename in os.listdir('templates/html'):
        pdfkit.from_file(
            f'templates/html/{filename}',
            f'templates/certificate/{Path(filename).stem}.pdf',
            configuration=pdfkit_config,
            options=options
        )
        os.remove(f'templates/html/{filename}')


def upload_certificate(folder_name) -> None:
    for filename in os.listdir('templates/certificate'):
        upload_file(
            f'templates/certificate/{Path(filename).stem}.pdf',
            f'certificates/{folder_name}/{Path(filename).stem}.pdf'
        )
        os.remove(f'templates/certificate/{Path(filename).stem}.pdf')


def create_sertificate(template_name, subtitle, date, names, folder):
    render_html(
        template_name,
        subtitle,
        date,
        names)
    to_pdf()
    upload_certificate(folder)
