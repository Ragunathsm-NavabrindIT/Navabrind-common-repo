import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


def get_response(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    return response