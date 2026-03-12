import os
import json
import requests
from datetime import datetime
import pytz

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
STATE_FILE = 'game_states.json'

def load_games():
    """Load games from config"""
    with open('config.json', 'r') as f:
        return json.load(f)['games']

def load_game_states():
    """Load previously tracked game states"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_game_states(states):
    """Save game states for next run"""
    with open(STATE_FILE, 'w') as f:
        json.dump(states, f)

def get_mlb_game_status(game_date):
    """Get all MLB games for a specific date with their status"""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date}&hydrate=linescore"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        games_status = []
        
        if 'dates' in data and len(data['dates']) > 0:
            for date_info in data['dates']:
                for game in date_info.get('games', []):
                    away_team = game['teams']['away']['team']['name']
                    home_team = game['teams']['home']['team']['name']
                    game_pk = game['gamePk']
                    
                    status = game['status']
                    detailed_state = status['detailedState']
                    abstract_state = status['abstractGameState']
                    reason = status.get('reason', '')
                    
                    # Get score and inning if game has started
                    linescore = game.get('linescore', {})
                    away_score = game['teams']['away'].get('score', 0)
                    home_score = game['teams']['home'].get('score', 0)
                    current_inning = linescore.get('currentInning', None)
                    inning_state = linescore.get('inningState', '')
                    
                    games_status.append({
                        'game_pk': game_pk,
                        'matchup': f"{away_team} vs {home_team}",
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_score': away_score,
                        'home_score': home_score,
                        'inning': current_inning,
                        'inning_state': inning_state,
                        'detailed_state': detailed_state,
                        'abstract_state': abstract_state,
                        'reason': reason
                    })
        
        return games_status
    except Exception as e:
        print(f"Error fetching MLB game status: {e}")
        return []

def is_weather_delay(game_status):
    """Check if game is in weather-related delay"""
    state = game_status['detailed_state'].lower()
    reason = game_status['reason'].lower()
    
    delay_keywords = ['delay', 'delayed', 'postponed', 'suspended']
    weather_keywords = ['rain', 'weather', 'storm', 'lightning', 'inclement']
    
    is_delayed = any(keyword in state for keyword in delay_keywords)
    is_weather = any(keyword in reason for keyword in weather_keywords) or \
                 any(keyword in state for keyword in weather_keywords)
    
    return is_delayed and is_weather

def format_score_inning(game_status):
    """Format score and inning info"""
    away = game_status['away_team']
    home = game_status['home_team']
    away_score = game_status['away_score']
    home_score = game_status['home_score']
    inning = game_status['inning']
    inning_state = game_status['inning_state']
    
    # Build score line
    score_text = f"{away} {away_score}, {home} {home_score}"
    
    # Add inning if game has started
    if inning:
        if inning_state == 'Middle':
            inning_text = f"Middle {inning}"
        elif inning_state == 'Top':
            inning_text = f"Top {inning}"
        elif inning_state == 'Bottom':
            inning_text = f"Bottom {inning}"
        elif inning_state == 'End':
            inning_text = f"End of {inning}"
        else:
            inning_text = f"Inning {inning}"
        
        return score_text, inning_text
    else:
        return None, None

def send_delay_alert(game_status, alert_type):
    """Send Slack alert for delay or resumption"""
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    
    if alert_type == "DELAY":
        emoji = "🚨"
        title = "RAIN DELAY DETECTED"
        text = f"🚨 Rain delay: {game_status['matchup']}"
    elif alert_type == "RESUME":
        emoji = "✅"
        title = "GAME RESUMING"
        text = f"✅ Game resuming: {game_status['matchup']}"
    elif alert_type == "POSTPONED":
        emoji = "📅"
        title = "GAME POSTPONED"
        text = f"📅 Game postponed: {game_status['matchup']}"
    else:
        emoji = "ℹ️"
        title = "GAME STATUS UPDATE"
        text = f"ℹ️ Status update: {game_status['matchup']}"
    
    message = {
        "text": text,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Game:*\n⚾ {game_status['matchup']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{game_status['detailed_state']}"
                    }
                ]
            }
        ]
    }
    
    # Add score and inning if available (for in-game delays)
    score_text, inning_text = format_score_inning(game_status)
    if score_text and alert_type in ["DELAY", "RESUME"]:
        message["blocks"].append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Score:*\n{score_text}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Inning:*\n{inning_text}"
                }
            ]
        })
    
    # Add reason if available
    if game_status['reason']:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:* {game_status['reason']}"
            }
        })
    
    # Add timestamp
    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"<!channel> Alert sent at {now.strftime('%I:%M %p')} PT"
            }
        ]
    })
    
    response = requests.post(SLACK_WEBHOOK, json=message)
    
    if response.status_code == 200:
        print(f"✅ {alert_type} alert sent for {game_status['matchup']}")
    else:
        print(f"❌ Failed to send alert: {response.status_code}")

def monitor_games():
    """Monitor games for status changes"""
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    
    previous_states = load_game_states()
    current_states = {}
    
    today = now.strftime('%Y-%m-%d')
    
    print(f"🔍 Monitoring MLB games for {today}...")
    
    games = get_mlb_game_status(today)
    
    if not games:
        print("No games found for today")
        return
    
    print(f"📅 Found {len(games)} game(s)")
    
    for game in games:
        game_pk = str(game['game_pk'])
        current_state = game['abstract_state']
        previous_state = previous_states.get(game_pk, {}).get('state')
        
        # NEW DELAY DETECTED
        if is_weather_delay(game) and previous_state != "DELAYED":
            print(f"🚨 NEW DELAY: {game['matchup']} - {game['detailed_state']}")
            send_delay_alert(game, "DELAY")
            current_states[game_pk] = {'state': 'DELAYED', 'matchup': game['matchup']}
        
        # GAME RESUMING
        elif previous_state == "DELAYED" and current_state == "Live":
            print(f"✅ RESUMING: {game['matchup']}")
            send_delay_alert(game, "RESUME")
            current_states[game_pk] = {'state': 'LIVE', 'matchup': game['matchup']}
        
        # GAME POSTPONED
        elif game['detailed_state'] == 'Postponed' and previous_state != "POSTPONED":
            print(f"📅 POSTPONED: {game['matchup']}")
            send_delay_alert(game, "POSTPONED")
            current_states[game_pk] = {'state': 'POSTPONED', 'matchup': game['matchup']}
        
        else:
            current_states[game_pk] = {'state': current_state, 'matchup': game['matchup']}
    
    save_game_states(current_states)
    print(f"\n✅ Monitoring complete - checked {len(games)} games")

def main():
    monitor_games()

if __name__ == "__main__":
    main()
