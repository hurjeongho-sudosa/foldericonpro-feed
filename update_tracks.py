#!/usr/bin/env python3
"""
스포티파이 아티스트 인기곡 순위를 조회해 tracks.txt 로 저장한다.
GitHub Actions에서 매일 실행된다.

Client ID / Secret 은 코드에 없고, GitHub 저장소의 Secrets 에서
환경변수로 주입된다. 따라서 저장소가 공개여도 비밀 값은 노출되지 않는다.

출력 형식 (FolderIconPro.exe 가 읽는 형식):
    #UPDATED=2026-08-23T20:00:00Z
    01|졸려 졸려|3:22
    02|간지러워|3:09
"""
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ARTIST_ID = os.environ.get("SPOTIFY_ARTIST_ID", "2RNEBUPa8YipjYIfCC4iuh")
MARKET = os.environ.get("SPOTIFY_MARKET", "KR")
OUT_PATH = os.environ.get("OUT_PATH", "tracks.txt")


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def get_token(client_id, client_secret):
    basic = base64.b64encode(
        (client_id + ":" + client_secret).encode("utf-8")
    ).decode("ascii")
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={
            "Authorization": "Basic " + basic,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        token = json.loads(r.read().decode("utf-8")).get("access_token")
    if not token:
        die("토큰 발급 실패 - Client ID / Secret 을 확인하세요")
    return token


def get_top_tracks(token):
    url = "https://api.spotify.com/v1/artists/{}/top-tracks?market={}".format(
        ARTIST_ID, MARKET
    )
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8")).get("tracks", [])


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        die("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET 이 설정되지 않았습니다")

    tracks = get_top_tracks(get_token(client_id, client_secret))
    if not tracks:
        die("인기곡이 0곡입니다 - 아티스트 ID를 확인하세요 (기존 tracks.txt 유지)")

    lines = ["#UPDATED=" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    lines.append("#ARTIST=" + ARTIST_ID)
    for i, t in enumerate(tracks, start=1):
        total = int(t.get("duration_ms", 0)) // 1000
        title = (t.get("name") or "").replace("|", "/").strip()
        if not title:
            continue
        lines.append("{:02d}|{}|{}:{:02d}".format(i, title, total // 60, total % 60))

    body = "\n".join(lines) + "\n"
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)

    print("{}곡 기록 완료 -> {}".format(len(tracks), OUT_PATH))
    print(body)


if __name__ == "__main__":
    main()
