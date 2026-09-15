import requests
import json
import math
import time
from datetime import datetime

# ===== 这里替换成你申请的 API Key =====
API_KEY = "9b43a838c7bc4e4891b22f9dcba02592" 
# ====================================
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

# 缓存球队数据，避免重复请求触发 API 限制
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

def get_team_recent_stats(team_id):
    """获取球队最近5场比赛的场均进球和失球"""
    if team_id in team_stats_cache:
        return team_stats_cache[team_id]
    
    try:
        url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit=5"
        res = requests.get(url, headers=headers)
        time.sleep(6) # 免费API限制每分钟10次，休眠6秒防止被限制
        
        if res.status_code == 200:
            matches = res.json().get("matches", [])
            if not matches:
                return 1.5, 1.5 # 如果没有近期数据，返回默认平均值
            
            goals_for = 0
            goals_against = 0
            for m in matches:
                if m['homeTeam']['id'] == team_id:
                    goals_for += m['score']['fullTime']['home']
                    goals_against += m['score']['fullTime']['away']
                else:
                    goals_for += m['score']['fullTime']['away']
                    goals_against += m['score']['fullTime']['home']
            
            avg_for = goals_for / len(matches)
            avg_against = goals_against / len(matches)
            team_stats_cache[team_id] = (avg_for, avg_against)
            return avg_for, avg_against
        else:
            print(f"获取球队 {team_id} 数据失败: {res.status_code}")
            return 1.5, 1.5
    except Exception as e:
        print(f"获取数据异常: {e}")
        return 1.5, 1.5

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/matches?dateFrom={today}&dateTo={today}"
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"获取今日比赛失败: {res.status_code}")
            return
        
        matches = res.json().get("matches", [])
        results = []
        
        for m in matches:
            home_id = m['homeTeam']['id']
            away_id = m['awayTeam']['id']
            home_name = m['homeTeam']['name']
            away_name = m['awayTeam']['name']
            league = m['competition']['name']
            
            # 获取球队近期数据
            home_attack, home_defense = get_team_recent_stats(home_id)
            away_attack, away_defense = get_team_recent_stats(away_id)
            
            pred = predict_match(home_attack, home_defense, away_attack, away_defense)
            
            results.append({
                "league": league,
                "time": m['utcDate'][11:16], # 提取比赛时间
                "home": home_name,
                "away": away_name,
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
