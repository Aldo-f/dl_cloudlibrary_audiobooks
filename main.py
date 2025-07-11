"""
CloudLibrary Audiobook Downloader

Download audiobooks from yourcloudlibrary.com after logging in with your library credentials.
This script automates borrowing, listing, and downloading MP3 audiobooks, including saving metadata.

Original project: https://github.com/Eshuigugu/dl_cloudlibrary_audiobooks

Features:
- Log in with barcode & PIN
- List currently borrowed items
- Optionally borrow a specific audiobook
- Download and save audiobook chapters as .mp3
- Save metadata as JSON
- Optionally return the book after download

Usage:
    python3 main.py -l LIBRARY -u USERNAME -p PASSWORD [--title MEDIA_ID] [--dump_json] [--release]

Example:
    python3 main.py -l examplelib -u 12345678 -p 0000 -t abcd123 --dump_json --release
"""

#!/usr/bin/python3
import requests
import json
import os
import re
import argparse
import getpass
from typing import List, Dict

session = requests.Session()
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://ebook.yourcloudlibrary.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="112", "Brave";v="112", "Not:A-Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://ebook.yourcloudlibrary.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

loaned_books_cache = {}


def cache_loaned_books(library: str):
    data = list_loaned_books(library, None, False)
    for item in data:
        book_id = item.get("itemId")
        if book_id:
            loaned_books_cache[book_id] = item
    print(f"Cached {len(loaned_books_cache)} loaned books")


def get_cached_book_metadata(book_id: str):
    if book_id in loaned_books_cache:
        return loaned_books_cache[book_id]
    else:
        raise KeyError(f"Book ID {book_id} not found in cache")


def log_in(library: str, username: str, password: str):
    headers = BASE_HEADERS.copy()
    headers.update(
        {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "nl",
            "Cache-Control": "no-cache",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Dnt": "1",
            "Pragma": "no-cache",
            "Referer": f"https://ebook.yourcloudlibrary.com/library/{library}/featured",
        }
    )

    data = {
        "action": "login",
        "barcode": username,
        "pin": password,
        "library": library,
    }

    login_url = "https://ebook.yourcloudlibrary.com/?_data=root"
    response = session.post(login_url, headers=headers, data=data)

    if response.status_code not in (200, 204):
        raise Exception(f"Login failed with status {response.status_code}")

    return response


def check_login(library: str):
    test_url = f"https://ebook.yourcloudlibrary.com/library/{library}/mybooks/current"
    response = session.get(test_url, allow_redirects=False)

    if response.is_redirect:
        raise Exception("Login failed: redirect to login page detected")

    if "__session_PROD" not in session.cookies.get_dict():
        raise Exception("Login failed: __session_PROD cookie not set")

    return True


def list_loaned_books(
    library: str, form_data: dict = None, use_cache: bool = True
) -> List[Dict]:
    if use_cache and loaned_books_cache:
        return list(loaned_books_cache.values())

    headers = BASE_HEADERS.copy()
    headers.update(
        {
            "accept-language": "nl",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "dnt": "1",
            "referer": f"https://ebook.yourcloudlibrary.com/library/{library}/mybooks/current",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
        }
    )

    if not form_data:
        form_data = {
            "format": "",
            "sort": "BorrowedDateDescending",
        }

    res = session.post(
        f"https://ebook.yourcloudlibrary.com/library/{library}/mybooks/current?_data=routes/library.$name.mybooks.current",
        data=form_data,
        headers=headers,
    )

    data = res.json()

    if "patronItems" not in data:
        raise ValueError("Response does not contain 'patronItems'")

    return data["patronItems"]


def return_book(book_id: str, library: str) -> bool:
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "nl",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Pragma": "no-cache",
        "Priority": "u=1, i",
        "Referer": f"https://ebook.yourcloudlibrary.com/library/{library}/detail/{book_id}",
        "Sec-Ch-Ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    }

    params = {
        "action": "return",
        "itemId": book_id,
        "_data": "routes/library.$name.detail.$id",
    }

    res = session.get(
        f"https://ebook.yourcloudlibrary.com/library/{library}/detail/{book_id}",
        params=params,
        headers=headers,
    )

    if res.status_code != 200:
        print(f"Return failed with status {res.status_code}")
        return False

    try:
        res_json = res.json()
    except Exception as e:
        print("Return JSON decode error:", e)
        print("Raw response text:", res.text[:500])
        return False

    if "error" in res_json:
        msg = res_json["error"].get("msg") or str(res_json["error"])
        print(f"Return failed: {msg}")
        return False

    if res_json.get("status") == "FAILED":
        print("Return status is FAILED")
        return False

    return True


def borrow_book(book_id: str, library: str) -> bool:
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "nl",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Pragma": "no-cache",
        "Priority": "u=1, i",
        "Referer": f"https://ebook.yourcloudlibrary.com/library/{library}/detail/{book_id}",
        "Sec-Ch-Ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    }

    params = {
        "action": "borrow",
        "itemId": book_id,
        "_data": "routes/library.$name.detail.$id",
    }

    res = session.get(
        f"https://ebook.yourcloudlibrary.com/library/{library}/detail/{book_id}",
        params=params,
        headers=headers,
    )

    if res.status_code != 200:
        print(f"Borrow failed with status {res.status_code}")
        return False

    try:
        res_json = res.json()
    except Exception as e:
        print("Borrow JSON decode error:", e)
        print("Raw response text:", res.text[:500])
        return False

    error = res_json.get("error")
    if error:
        if error.get("reaktorErrorMessage") == "TOO_MANY_LOANS":
            if loaned_books_cache:
                to_return = next(iter(loaned_books_cache))
                print(f"Returning book {to_return}")
                if return_book(to_return, library):
                    cache_loaned_books(library)
                    return borrow_book(book_id, library)
                else:
                    print("Return failed")
            else:
                print("Nothing to return")
        else:
            print(f"Borrow failed: {error.get('msg') or error}")
        return False

    if res_json.get("status") == "FAILED":
        print("Borrow status is FAILED")
        return False

    return True


def filter_loaned_books(media_ids: list, library: str):
    loaned_books = list_loaned_books(library)
    return [x for x in loaned_books if x["itemId"] in media_ids]


def get_book_metadata_brief(library: str, media_id: str, use_cache=True):
    if use_cache:
        cached = loaned_books_cache.get(media_id)
        if cached:
            return cached

    headers = BASE_HEADERS.copy()
    headers.update(
        {
            "accept-language": "nl",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "dnt": "1",
            "referer": f"https://ebook.yourcloudlibrary.com/library/{library}/mybooks/current",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
        }
    )

    url = (
        f"https://ebook.yourcloudlibrary.com/library/{library}/detail/{media_id}?_data"
    )
    res = session.get(url, headers=headers)

    if res.status_code == 403:
        raise PermissionError(f"403 Forbidden on {url}. Check session cookies.")

    data = res.json()
    book = data.get("book")
    if not book:
        with open("metadata_error_dump.json", "w") as f:
            import json

            json.dump(data, f, indent=2)
        raise KeyError("'book' not found. Dumped to metadata_error_dump.json")

    return book


def download_book(loaned_book: dict, library: str, dump_json=False):
    book_id = loaned_book["itemId"]
    audiobook_meta_brief = get_book_metadata_brief(library, book_id)
    title = audiobook_meta_brief["title"]

    fulfillment_url = (
        f"https://audio.yourcloudlibrary.com/listen/{book_id}?_data=routes/listen.$id"
    )

    headers = {
        "authority": "audio.yourcloudlibrary.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://ebook.yourcloudlibrary.com/",
        "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-site",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }

    audiobook_loan = session.get(fulfillment_url, headers=headers).json()["audiobook"]
    fulfillment_id = audiobook_loan["fulfillmentId"]

    metadata_url = f'https://api.findawayworld.com/v4/accounts/{audiobook_loan["accountId"]}/audiobooks/{fulfillment_id}'

    cross_site_headers = HEADERS.copy()
    cross_site_headers.update(
        {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Sec-Fetch-Site": "cross-site",
            "Session-Key": audiobook_loan["sessionKey"],
        }
    )

    audiobook_metadata = session.get(metadata_url, headers=cross_site_headers).json()[
        "audiobook"
    ]

    audiobook_playlist = session.post(
        f"https://api.findawayworld.com/v4/audiobooks/{fulfillment_id}/playlists",
        headers=cross_site_headers,
        data=json.dumps({"license_id": audiobook_loan["licenseId"]}),
    ).json()["playlist"]

    first_author = (
        audiobook_metadata["authors"][0] if audiobook_metadata["authors"] else ""
    )

    folder_name = f"{book_id} - {first_author} - {title}"
    folder_name = re.sub(r"[^\w\-_. ]", "", folder_name).strip()[:100]
    output_directory = os.path.join("audiobooks", folder_name)

    os.makedirs(output_directory, exist_ok=True)

    max_chapter_idx_length = len(str(len(audiobook_loan["items"])))
    chapter_idx = 1

    # download all the audio files
    for chapter, chapter_info in zip(audiobook_playlist, audiobook_loan["items"]):
        file_ext = chapter["url"][::-1].split(".")[0][::-1]
        output_filename = (
            f"%0{max_chapter_idx_length}d - " % chapter_idx + chapter_info["title"]
        )
        chapter_idx += 1
        output_filename += f".{file_ext}"

        output_filepath = os.path.join(output_directory, output_filename)
        if os.path.exists(output_filepath):
            print(output_filepath, "exists. skipping")
            continue
        r = session.get(chapter["url"], headers=cross_site_headers)
        print(f"downloading to {output_filepath}")
        with open(output_filepath, "wb") as f:
            f.write(r.content)

    subtitle = audiobook_meta_brief.get("SubTitle")
    if subtitle and subtitle.lower() == "a novel":
        subtitle = None

    series = []
    for series_string in audiobook_metadata.get("series", []):
        match = re.search(r" #(\d+)$", series_string)
        if match:
            number = match.group(1)
            name = series_string[: match.start()]
        else:
            number = ""
            name = series_string
        series.append({"name": name, "number": number})

    fast_fillout = {
        "authors": audiobook_metadata.get("authors", []),
        "title": f"{title}: {subtitle}" if subtitle else title,
        "isbn": audiobook_meta_brief.get("isbn"),
        "description": audiobook_meta_brief.get("description"),
        "narrator": audiobook_metadata.get("narrators", []),
        "language": audiobook_metadata.get("language"),
        "thumbnail": audiobook_metadata.get("cover_url"),
        "series": series,
    }

    print("Fast Fillout JSON:\n" + json.dumps(fast_fillout))

    if dump_json:
        merged_metadata = audiobook_meta_brief.copy()
        merged_metadata.update(audiobook_metadata)
        merged_metadata["chapters"] = audiobook_loan["items"]
        with open(os.path.join(output_directory, f"{book_id}.json"), "w") as f:
            json.dump(merged_metadata, f, indent=2)

    return output_directory


def download_books(library, return_books=False, dump_json=False, media_id=None):
    """
    Download one or more audiobooks from CloudLibrary.

    Args:
        library (str): Name of the library as used in the CloudLibrary URL.
        username (str): Library card number or username.
        password (str): PIN or password.
        return_books (bool): Whether to return the book after downloading.
        dump_json (bool): Whether to export metadata as JSON.
        media_id (str or None): Specific book to download; if not provided, downloads all MP3 loans.

    Yields:
        str: Directory path where each downloaded audiobook is saved.
    """

    # Cache all loaned books immediately after login
    cache_loaned_books(library)

    if media_id:
        media_meta_brief = get_book_metadata_brief(library, media_id)
        if media_meta_brief["mediaType"] != "Mp3":
            raise Exception(f"MediaType != Mp3 {media_meta_brief['mediaType']}")

    # if user gave a media id, download that one. otherwise download all loaned books.
    if media_id:
        # list loaned books
        books_to_download = filter_loaned_books([media_id], library)
        if not books_to_download:
            print(f"Borrowing book {media_id}")
            if media_meta_brief["status"] != "CAN_LOAN":
                raise Exception("Can't borrow book")
            success = borrow_book(book_id=media_id, library=library)
            if not success:
                exit(1)
            cache_loaned_books(library)
            books_to_download = filter_loaned_books([media_id], library)
    else:
        books_to_download = [
            x for x in list_loaned_books(library) if x["mediaType"] == "Mp3"
        ]

    for book_to_download in books_to_download:
        yield download_book(book_to_download, library, dump_json=dump_json)
        if return_books:
            return_book(book_to_download["itemId"], library)


def get_initial_cookies(library: str):
    url = f"https://ebook.yourcloudlibrary.com/library/{library}/featured"
    res = session.get(url)
    cookies = session.cookies.get_dict()
    if "__config_PROD" not in cookies:
        raise Exception("__config_PROD cookie not found after initial request")
    return cookies["__config_PROD"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--library", type=str, help="Library name")
    parser.add_argument(
        "-u", "--username", type=str, help="Library card number / barcode"
    )
    parser.add_argument("-p", "--password", type=str, help="Password / PIN")
    parser.add_argument(
        "--prompt_password",
        action="store_true",
        help="Prompt for password interactively",
    )
    parser.add_argument(
        "-t", "--title", type=str, help="Media ID of the title to download"
    )
    parser.add_argument(
        "--dump_json", action="store_true", help="Dump metadata as JSON file"
    )
    parser.add_argument(
        "--release", action="store_true", help="Return selected books after download"
    )
    parser.add_argument(
        "-c", "--cookie", type=str, help="Optional __session_PROD cookie to skip login"
    )

    args = parser.parse_args()

    library = args.library or input("Enter library name: ")

    config_cookie = get_initial_cookies(library)
    session.cookies.set("__config_PROD", config_cookie)

    if args.cookie:
        session.cookies.set("__session_PROD", args.cookie)
        username = None
        password = None
    else:
        username = args.username or input("Enter username / barcode: ")
        if args.prompt_password or not args.password:
            password = getpass.getpass("Enter password: ")
        else:
            password = args.password
        log_in(library=library, username=username, password=password)

    check_login(library=library)

    for download in download_books(
        library=library,
        return_books=args.release,
        dump_json=args.dump_json,
        media_id=args.title,
    ):
        print(f"downloaded {download}")
