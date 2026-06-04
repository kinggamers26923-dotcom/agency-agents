import os
import re
import webbrowser
from pathlib import Path

from .telegram_service import send_document as telegram_send_document


def get_search_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        Path(os.getenv("JARVIS_SEARCH_ROOT_1", home / "Desktop")),
        Path(os.getenv("JARVIS_SEARCH_ROOT_2", home / "Downloads")),
        Path(os.getenv("JARVIS_SEARCH_ROOT_3", home / "Documents")),
        Path(os.getenv("JARVIS_SEARCH_ROOT_4", Path.cwd())),
    ]
    return [path for path in candidates if path.exists()]


def normalize_query(query: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", query.lower()))


def match_filename(filename: str, query: str) -> bool:
    terms = normalize_query(query).split()
    lower = filename.lower()
    return all(term in lower for term in terms)


def search_local_files(query: str, max_results: int = 8) -> list[str]:
    roots = get_search_roots()
    matches: list[str] = []
    if not roots:
        return []

    for root in roots:
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                if len(matches) >= max_results:
                    return matches
                if match_filename(filename, query):
                    matches.append(os.path.join(dirpath, filename))
            if len(matches) >= max_results:
                break
    return matches


def open_web_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = f"https://{url}"
    # new=0: reuse existing tab/window if possible; new=1: always new window (prevents multi-tab spam)
    webbrowser.open(url, new=0)
    return url


def open_local_path(path: str) -> str:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"Path not found: {resolved}")
    os.startfile(resolved)
    return str(resolved)


def handle_command(command: str) -> dict:
    text = command.strip()
    if not text:
        return {"success": False, "message": "Please type a command for Jarvis."}

    lower = text.lower()
    if "send file" in lower and "telegram" in lower:
        match = re.search(r"send file\s+(.+?)\s+to\s+telegram\s+(.+)", text, re.IGNORECASE)
        if match:
            file_path = match.group(1).strip().strip('"')
            chat_id = match.group(2).strip()
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not token:
                return {"success": False, "message": "Telegram bot token is not configured in the environment."}
            if not Path(file_path).exists():
                return {"success": False, "message": f"File not found: {file_path}"}
            try:
                telegram_send_document(token, chat_id, file_path, caption="Jarvis sending requested file")
                return {"success": True, "action": "send_file", "message": f"Sent file to Telegram chat {chat_id}."}
            except Exception as exc:
                return {"success": False, "message": f"Failed to send file: {exc}"}
        return {"success": False, "message": "Please provide a file path and Telegram chat ID, e.g. send file C:\\path\\file.mp4 to telegram 12345."}

    if "find file" in lower or "search file" in lower or "youtube file" in lower or ("search" in lower and "file" in lower):
        query = re.sub(r'^(?:.*?\b(?:find|search)\b(?:\s+file(?:s)?|\s+for)?\s*)', '', lower).strip()
        if not query:
            query = "youtube"
        results = search_local_files(query)
        if results:
            return {
                "success": True,
                "action": "search",
                "message": f"Found {len(results)} file(s) matching '{query}'.",
                "files": results,
            }
        return {"success": True, "action": "search", "message": f"No files found matching '{query}'.", "files": []}

    # File/folder opening: Check BEFORE URL to avoid matching file extensions as domains
    if "open file" in lower or ("open" in lower and "folder" in lower and "." not in text):
        if "open file" in lower:
            path_match = re.search(r"open (?:file )?(.+)", text, re.IGNORECASE)
            if path_match:
                candidate = path_match.group(1).strip().strip('"')
                try:
                    opened = open_local_path(candidate)
                    return {"success": True, "action": "open_file", "message": f"Opened file or folder: {opened}"}
                except FileNotFoundError as exc:
                    return {"success": False, "action": "open_file", "message": str(exc)}
        
        if "folder" in lower:
            path_match = re.search(r"open (?:the )?folder (.+)", text, re.IGNORECASE)
            if path_match:
                candidate = path_match.group(1).strip().strip('"')
                try:
                    opened = open_local_path(candidate)
                    return {"success": True, "action": "open_folder", "message": f"Opened folder: {opened}"}
                except FileNotFoundError as exc:
                    return {"success": False, "action": "open_folder", "message": str(exc)}

    # URL opening: "open youtube.com", "open https://...", "open www.example.com"
    url_match = re.search(r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9][a-zA-Z0-9-]*(?:\.[a-zA-Z0-9][a-zA-Z0-9-]*)+\b)", text)
    if "open" in lower and url_match:
        url = url_match.group(0)
        opened = open_web_url(url)
        return {"success": True, "action": "open_url", "message": f"Opened URL: {opened}"}

    if "open file" in lower or "open" in lower and "." in lower:
        path_match = re.search(r"open (?:file )?(.+)", text, re.IGNORECASE)
        if path_match:
            candidate = path_match.group(1).strip().strip('"')
            try:
                opened = open_local_path(candidate)
                return {"success": True, "action": "open_file", "message": f"Opened file or folder: {opened}"}
            except FileNotFoundError as exc:
                return {"success": False, "action": "open_file", "message": str(exc)}

    if "open" in lower and "folder" in lower:
        path_match = re.search(r"open (?:the )?folder (.+)", text, re.IGNORECASE)
        if path_match:
            candidate = path_match.group(1).strip().strip('"')
            try:
                opened = open_local_path(candidate)
                return {"success": True, "action": "open_folder", "message": f"Opened folder: {opened}"}
            except FileNotFoundError as exc:
                return {"success": False, "action": "open_folder", "message": str(exc)}

    if "list" in lower and "file" in lower and "desktop" in lower:
        roots = [str(root) for root in get_search_roots()]
        return {"success": True, "action": "list_roots", "message": "Search roots used by Jarvis.", "roots": roots}

    # Detect if this looks like a general question rather than a desktop command
    question_keywords = ['what', 'who', 'where', 'when', 'why', 'how', 'give me', 'tell me', 'news', 'weather', 'define', 'explain']
    if any(keyword in lower for keyword in question_keywords):
        return {
            "success": False,
            "action": "suggest_ai_draft",
            "message": f"'{text}' looks like a general question. Use the 'Create AI Draft' feature above to ask Jarvis questions about anything.",
        }

    return {
        "success": False,
        "message": "Jarvis command not recognized. Supported desktop commands:\n• find/search files: 'find youtube files', 'search file report'\n• open URLs: 'open youtube.com', 'open https://example.com'\n• open files: 'open file C:\\\\Users\\\\...\\\\video.mp4'\n• send to Telegram: 'send file C:\\\\path\\\\file.mp4 to telegram 12345'\n\nFor questions, news, or anything else, use the 'Create AI Draft' feature instead.",
    }
