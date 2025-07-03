# 🎧 CloudLibrary Audiobook Downloader

A command-line tool to download audiobooks from [yourcloudlibrary.com](https://ebook.yourcloudlibrary.com).

This script allows you to:

- Log in with your library account
- List currently borrowed audiobooks
- Optionally borrow a specific audiobook
- Download MP3 files of audiobook chapters
- Save metadata in `.json` format
- Optionally return books after downloading

---

## ⚙️ Installation

Make sure you have Python 3 and install dependencies:

```bash
pip install -r requirements.txt
```

Or just install `requests`:

```bash
pip install requests
```

---

## ▶️ Usage

You can authenticate using **two methods**:

### 1. Login with username and password

```bash
python3 main.py -l LIBRARY -u USERNAME -p PASSWORD [OPTIONS]
```

### 2. Skip login by providing an existing session cookie (__session_PROD)

```
python3 main.py -l LIBRARY -c COOKIE_VALUE [OPTIONS]
```


### Options:

| Argument            | Description                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------ |
| `-l`, `--library`   | Name of the library (as seen in the URL)                                                         |
| `-u`, `--username`  | Your barcode or login username                                                                   |
| `-p`, `--password`  | Your PIN or password                                                                             |
| `--prompt_password` | Prompt for password input instead of using `-p`                                                  |
| `-t`, `--title`     | Media ID of a specific title to download (optional)                                              |
| `--dump_json`       | Save full metadata as `.json` file                                                               |
| `--release`         | Return the book(s) after downloading                                                             |
| `--c`, `--cookie`   | Optional `__session_PROD` cookie to skip login (if provided, username/password are not required) |

### Example:

```bash
python3 main.py -l mylib -u 12345678 -p 0000 --title abc123 --dump_json --release
```

---

## 📂 Output

- Each audiobook is saved in a directory named:  
  `MEDIAID - Author - Title`
- MP3 files are numbered by chapter
- Optional `.json` file contains metadata

---

## 📝 Metadata Example (`--dump_json`)

If enabled, the script generates metadata like this:

```json
{
  "authors": ["Author Name"],
  "title": "Book Title",
  "isbn": "9781234567890",
  "description": "Book description...",
  "narrator": ["Narrator Name"],
  "language": "eng",
  "thumbnail": "https://...jpg",
  "series": [{"name": "Series Name", "number": "1"}]
}
```

---

## 💡 Tip

You can extract the media ID from the book's URL, e.g.:

```
https://ebook.yourcloudlibrary.com/library/mylib/detail/**ABC123**
```

Use `ABC123` as the media ID with the `--title` flag.

---

## 📜 License

MIT License

Based on [https://github.com/Eshuigugu/dl_cloudlibrary_audiobooks](https://github.com/Eshuigugu/dl_cloudlibrary_audiobooks)