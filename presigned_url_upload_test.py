import logging
import requests

DEFAULT_FILE_NAME = 'testfile.jpg'
DEFAULT_FILE_PATH = '/home/grgr/Downloads/filtr-do-kawy-westmark-6-tz-czarny_897920_2568076_350x350w50.jpg'


def get_url(file_name=DEFAULT_FILE_NAME):
    BASE_URL = 'http://127.0.0.1:8000'
    ENDPOINT_URL = '/api/get_upload_url/'
    FULL_URL = BASE_URL + ENDPOINT_URL

    data = {
        'to': 'clients',
        'id': '4',
        'file_name': file_name
    }

    return requests.get(
        url=FULL_URL, data=data).json()


def post_file_to_presigned_url(response_with_url, file_path=DEFAULT_FILE_PATH):
    file = file_path
    with open(file, 'rb') as f:
        files = {'file': (file, f)}
        response = requests.post(
            response_with_url['url'],
            data=response_with_url['fields'],
            files=files)

    logging.info(f'File upload HTTP status code: {response.status_code}')
    return response


post_file_to_presigned_url(get_url())
