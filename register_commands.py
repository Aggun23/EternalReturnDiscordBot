#!/usr/bin/env python3
"""
디스코드에 슬래시 명령어(/쿠폰 /스킨 /패치 /영상)를 등록한다. 처음 한 번, 그리고 명령어를 바꿨을 때만 실행.

환경 변수
  DISCORD_APP_ID     디스코드 개발자 포털 → General Information → APPLICATION ID
  DISCORD_BOT_TOKEN  디스코드 개발자 포털 → Bot → Reset Token 으로 받은 토큰
"""

import json
import os
import sys
import urllib.error
import urllib.request

COMMANDS = [
    {
        "type": 1,
        "name": "쿠폰",
        "description": "지금 쓸 수 있는 이터널 리턴 쿠폰",
    },
    {
        "type": 1,
        "name": "스킨",
        "description": "최근 스킨 소식 (캐릭터 이름을 넣으면 그 캐릭터만)",
        "options": [
            {"type": 3, "name": "캐릭터", "description": "예: 아야, 수아, 니키", "required": False},
        ],
    },
    {
        "type": 1,
        "name": "패치",
        "description": "최근 패치노트 · 핫픽스",
    },
    {
        "type": 1,
        "name": "영상",
        "description": "최근 스킨 · 시즌 영상",
    },
]


def main():
    app_id = os.environ.get("DISCORD_APP_ID", "").strip()
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not app_id or not token:
        sys.exit("DISCORD_APP_ID 와 DISCORD_BOT_TOKEN 을 넣어 주세요.")

    req = urllib.request.Request(
        f"https://discord.com/api/v10/applications/{app_id}/commands",
        data=json.dumps(COMMANDS).encode("utf-8"),
        method="PUT",  # 목록 전체를 이걸로 덮어씀 (여러 번 실행해도 안전)
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com, 1.3)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        hint = {
            401: "봇 토큰이 틀렸어요. Bot 탭에서 Reset Token으로 새로 받아 Secret을 바꿔 주세요.",
            403: "APPLICATION ID와 봇 토큰이 서로 다른 앱 것인지 확인해 주세요.",
            404: "APPLICATION ID가 틀렸어요.",
        }.get(e.code, "")
        sys.exit(f"등록 실패 (HTTP {e.code}) {hint}\n{body[:500]}")

    print("등록된 명령어: " + ", ".join("/" + c["name"] for c in result))
    print("디스코드에서 / 를 쳐 보세요. 바로 안 보이면 디스코드를 새로고침(Ctrl+R)하면 돼요.")


if __name__ == "__main__":
    main()
