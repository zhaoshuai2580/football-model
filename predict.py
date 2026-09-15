import requests
import json
import math
from datetime import datetime

API_KEY = "你的API_KEY"
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

def poisson(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def predict_match(home_attack, home_defense, away_attack, away_defense):
    home_advantage = 1.10
    lam_home = (home_attack + away_defense) / 2 * home_advantage
    lam_away = (away_attack + home_defense) / 2
    p_home = p_draw = p_away = 0
    for i in range(7):
        for j in range(7):
            p = poisson(i, lam_home) * poisson(j, lam_away)
            if i > j: p_home += p
            elif i == j: p_draw += p
            else: p_away += p
    total = p_home + p_draw + p_away
    return {
        "home_win": round(p_home/total*100, 1),
        "draw": round(p_draw/total*100, 1),
        "away_win": round(p_away/total*100, 1),
        "score": f"{round(lam_home, 2)}:{round(lam_away, 2)}"
    }

def main():
    # 这里为了方便你测试，先写死两场比赛。后续接 API 会自动替换
    matches = [
        {"league": "示例联赛", "time": "20:00", "home": "主队A", "away": "客队A"},
        {"league": "示例联赛", "time": "22:00", "home": "主队B", "away": "客队B"}
    ]
    results = []
    for m in matches:
        pred = predict_match(1.5, 1.1, 1.2, 1.3)
        results.append({
            "league": m["league"],
            "time": m["time"],
            "home": m["home"],
            "away": m["away"],
            "home_win": pred["home_win"],
            "draw": pred["draw"],
            "away_win": pred["away_win"],
            "score": pred["score"]
        })

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "matches": results
        }, f, ensure_ascii=False, indent=2)
    print("预测数据生成完毕")

if __name__ == "__main__":
    main()
