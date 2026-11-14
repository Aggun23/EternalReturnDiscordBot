#!/usr/bin/env python3
"""
디스코드에 슬래시 명령어(/쿠폰 /스킨 /패치 /패치노트 /영상 /쿠폰추가 /쿠폰삭제)를 등록한다. 처음 한 번, 그리고 명령어를 바꿨을 때만 실행.

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
            {"type": 3, "name": "캐릭터", "description": "캐릭터 이름 (예: 블레어). 비워 두면 최근 스킨 소식 전체",
             "required": False, "autocomplete": True, "max_length": 30},
        ],
    },
    {
        "type": 1,
        "name": "패치",
        "description": "최근 패치노트 · 핫픽스",
    },
    {
        "type": 1,
        "name": "패치노트",
        "description": "패치노트 요약 (이름을 넣으면 그 캐릭터·아이템·변경사항만 자세히)",
        "options": [
            {"type": 3, "name": "이름", "description": "캐릭터·아이템 이름 (예: 블레어) 또는 실험체 / 아이템 / 변경사항 / 핫픽스. 비워 두면 한눈에 보기",
             "required": False, "autocomplete": True, "max_length": 100},
            {"type": 3, "name": "버전", "description": "패치 버전 (예: 13.0). 비워 두면 가장 최근 패치",
             "required": False, "autocomplete": True, "max_length": 20},
        ],
    },
    {
        "type": 1,
        "name": "영상",
        "description": "최근 스킨 · 시즌 영상",
    },
    {
        "type": 1,
        "name": "쿠폰추가",
        "description": "쿠폰 직접 등록 (/쿠폰 목록 + 마감 하루 전 알림에 들어감)",
        "default_member_permissions": "32",  # 서버 관리 권한이 있는 사람에게만 보임
        "contexts": [0],                     # 서버 안에서만
        "options": [
            {"type": 3, "name": "코드", "description": "쿠폰 코드 (예: GLORYBLAIR)", "required": True,
             "min_length": 4, "max_length": 30},
            {"type": 3, "name": "기한", "description": "예: 11/30 또는 11/30 23:59 또는 11월 30일 오전 5시 (안 쓰면 30일 동안 표시)",
             "max_length": 50},
            {"type": 3, "name": "보상", "description": "예: 블레어 스킨, 골드 500 (선택)", "max_length": 100},
        ],
    },
    {
        "type": 1,
        "name": "쿠폰삭제",
        "description": "직접 등록한 쿠폰 지우기",
        "default_member_permissions": "32",
        "contexts": [0],
        "options": [
            {"type": 3, "name": "코드", "description": "지울 쿠폰 코드", "required": True, "autocomplete": True},
        ],
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
