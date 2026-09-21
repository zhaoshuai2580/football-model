import os
import requests
import json
import math
import time
from datetime import datetime

# ===== 这里替换成你申请的球小策 API Key =====
API_KEY = "os.environ.get("QIUXIAOCE_API_KEY", "默认Key如果没有就填这里")"
# ==========================================
BASE_URL = "https://api.qiuxiaoce.com/v1"
headers = {"Authorization": f"Bearer {API_KEY}"}

team_stats_cache = {}

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

def get_match_pack(fixture_id):
    """获取单场赛前全景数据包"""
    try:
        url = f"{BASE_URL}/match-pack/{fixture_id}"
        res = requests.get(url, headers=headers)
        time.sleep(2) 
        if res.status_code == 200:
            data = res.json().get("data", {})
            home_attack = data.get("home_attack_avg", 1.5)
            home_defense = data.get("home_defense_avg", 1.2)
            away_attack = data.get("away_attack_avg", 1.3)
            away_defense = data.get("away_defense_avg", 1.4)
            return home_attack, home_defense, away_attack, away_defense
        else:
            print(f"获取比赛 {fixture_id} 数据失败: {res.status_code}")
            return 1.5, 1.2, 1.3, 1.4
    except Exception as e:
        print(f"获取数据异常: {e}")
        return 1.5, 1.2, 1.3, 1.4

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 获取今日赛程快讯与彩票编号
    url = f"{BASE_URL}/today-digest"
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"获取今日比赛失败: {res.status_code}")
            return
        
        matches = res.json().get("data", {}).get("fixtures", [])
        results = []
        
        for m in matches:
            fixture_id = m['fixture_id']
            home_name = m['home_team']
            away_name = m['away_team']
            league = m['league_name']
            lottery_num = m.get('lottery_num', '')
            
            home_attack, home_defense, away_attack, away_defense = get_match_pack(fixture_id)
            pred = predict_match(home_attack, home_defense, away_attack, away_defense)
            
            results.append({
                "league": league,
                "time": m.get('kickoff_time', ''),
                "home": home_name,
                "away": away_name,
                "lottery_num": lottery_num,
                "home_win": pred["home_win"],
                "draw": pred["draw"],
                "away_win": pred["away_win"],
                "score": pred["score"]
            })
            
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({
                "date": today,
                "matches": results
            }, f, ensure_ascii=False, indent=2)
        print(f"成功生成 {len(results)} 场比赛预测")
        
    except Exception as e:
        print(f"运行出错: {e}")

if __name__ == "__main__":
    main()
