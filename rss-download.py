#!/usr/bin/env python3

import re
import requests
import xml.etree.ElementTree as ET
import os
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import List, Any, Dict, Optional


def extract_id(url: str) -> str | None:
    """
    Extracts the ID following 'sq_' and preceding the next '_' from the given URL.
    """
    match = re.search(r"sq_(f\d+)_", url)
    return match.group(1) if match else None


def build_feed_url(ivoox_id: str) -> str:
    """
    Builds the feed URL using the extracted ID.
    """
    return f"https://feeds.ivoox.com/feed_fg_{ivoox_id}_filtro_1.xml"

def get_first_mp3_enclosure(feed_url: str) -> str | None:
    """Fetch RSS feed, parse XML, and return the first .mp3 enclosure URL (or None if none found)."""
    resp = requests.get(feed_url)
    resp.raise_for_status()
    xml_data = resp.content

    root = ET.fromstring(xml_data)
    # RSS structure: <rss><channel><item>⋯</item><item>…
    # find first <item>
    channel = root.find("channel")
    if channel is None:
        return None
    item = channel.find("item")
    if item is None:
        return None

    # find enclosure tag inside item
    enclosure = item.find("enclosure")
    if enclosure is None:
        return None

    url = enclosure.get("url")
    # Optionally check if it ends with .mp3
    if url and url.lower().endswith(".mp3"):
        return url
    return url  # or None if you want to require .mp3

def download_mp3(mp3_url: str, dest_folder: str) -> str:
    """
    Downloads an MP3 file from mp3_url and stores it in dest_folder.
    Returns the full path of the saved file.
    """
    # Ensure destination folder exists
    os.makedirs(dest_folder, exist_ok=True)

    # Extract filename from URL
    filename = mp3_url.split("/")[-1]
    # If filename doesn't end with .mp3 but contains .mp3 (e.g. "ep.mp3?download=1"), strip suffix after .mp3
    if not filename.lower().endswith(".mp3"):
        idx = filename.lower().find(".mp3")
        if idx != -1:
            filename = filename[: idx + 4]  # keep the '.mp3' part
    dest_path = os.path.join(dest_folder, filename)

    # Stream-download the file
    with requests.get(mp3_url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)

    return dest_path


@dataclass
class PodcastConfig:
    downloaded_podcast_audio: Path
    podcast_url: List[str]


class ConfigLoader:
    """
    Loads a YAML configuration file containing:
    - downloaded_podcast_audio: string (path)
    - podcast_url: array of strings (RSS feed URLs)
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Optional[PodcastConfig] = None

    def load(self) -> PodcastConfig:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        data = self._read_yaml()
        self._validate(data)

        self.config = PodcastConfig(
            downloaded_podcast_audio=Path(data["downloaded_podcast_audio"]),
            podcast_url=data["podcast_url"]
        )
        return self.config

    def _read_yaml(self) -> Dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _validate(data: Dict[str, Any]):
        if "downloaded_podcast_audio" not in data:
            raise ValueError("Missing required field: downloaded_podcast_audio")
        if "podcast_url" not in data:
            raise ValueError("Missing required field: podcast_url")
        if not isinstance(data["podcast_url"], list):
            raise ValueError("podcast_url must be an array of strings")


if __name__ == "__main__":
    loader = ConfigLoader("config.yaml")
    config = loader.load()

    print(config.downloaded_podcast_audio)
    print(config.podcast_url)

    for podcast_url in config.podcast_url:
        ivoox_id = extract_id(podcast_url)
        if ivoox_id:
            feed_url = build_feed_url(ivoox_id)
            print(feed_url)
        else:
            print("ID not found")

        mp3_url = get_first_mp3_enclosure(feed_url)
        print("First MP3 URL:", mp3_url)
        saved_file = download_mp3(mp3_url, 'downloaded_podcast_audio')
        print("Saved:", saved_file)

