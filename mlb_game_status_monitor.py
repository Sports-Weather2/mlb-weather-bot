import os
import json
import requests
from datetime import datetime
import pytz
from analytics import log_alert, log_workflow_run

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

def get_venue_info_from_game(game):
    """Extract venue name and roof type from MLB game data"""
    venue = game.get('venue', {})
    venue_name = venue.get('name', 'Unknown Venue')
    
    # Determine roof type
    roof_info = get_venue_roof_type(venue_name)
    
    return {
        'name': venue_name,
        'roof_type': roof_info['type'],
        'roof_description': roof_info['description']
    }

def get_venue_roof_type(venue_name):
    """Determine roof type for a venue"""
    fixed_domes = {
        'Tropicana Field': {'type': 'fixed_dome', 'description': '🏟️ Fixed Dome'},
        'Rogers Centre': {'type': 'fixed_dome', 'description': '🏟️ Fixed Dome'}
    }
    
    retractable_roofs = {
        'Chase Field': {'type': 'retractable', 'description': '🔄 Retractable Roof'},
        'loanDepot park': {'type': 'retractable', 'description': '🔄 Retractable Roof'},
        'Globe Life Field': {'type': 'retractable', 'description': '🔄 Retractable Roof'},
        'Minute Maid Park': {'type': 'retractable', 'description': '🔄 Retractable Roof'},
        'T-Mobile Park': {'type': 'retractable', 'description': '🔄 Retractable Roof'},
        'American Family Field': {'type': 'retractable', 'description': '🔄 Retractable Roof'}
    }
    
    if venue_name in fixed_domes:
        return fixed_domes[venue_name]
    
    if venue_name in retractable_roofs:
        return retractable_roofs[venue_name]
    
    return {'type': 'open_air', 'description': '☀️ Open Air'}

def should_monitor_game(game, venue_info):
    """
    Determine if we should monitor a game based on roof status.
    
    Strategy for real-time monitoring:
    - Fixed domes: Still monitor (non-weather delays can happen)
    - Retractable roofs: Always monitor (roof could be open)
    - Open-air: Always monitor
    
    This returns True for all games since we only alert on actual state changes.
    Roof info is added to alerts for context.
    """
    # Monitor all games - we only alert when delays/postponements actually happen
    # Roof info is included in alerts for operational context
    return True

def get_mlb_game_status(game_date):
    """Get all MLB games for a specific date with their status"""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date}&hydrate=linescore,venue"
    
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
                    
                    # Get venue information
                    venue_info = get_venue_info_from_game(game)
                    
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
                        'reason': reason,
                        'venue': venue_info
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
    
    venue = game_status.get('venue', {})
    venue_name = venue.get('name', 'Unknown Venue')
    roof_description = venue.get('roof_description', '')
    
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
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Venue:*\n{venue_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Stadium Type:*\n{roof_description}"
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
    
    # Add operational note for roofed stadiums
    if venue.get('roof_type') in ['fixed_dome', 'retractable']:
        if alert_type in ["DELAY", "POSTPONED"]:
            if venue.get('roof_type') == 'retractable':
                note = "⚠️ *Note:* Stadium has retractable roof - may have been open or roof malfunction"
            else:
                note = "⚠️ *Note:* Fixed dome stadium - delay likely non-weather related"
            
            message["blocks"].append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": note
                    }
                ]
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
        print(f"✅ {alert_type} alert sent for {game_status['matchup']} at {venue_name}")
        
        # ✅ LOG ANALYTICS
        if alert_type == "DELAY":
            log_alert('delay')
        elif alert_type == "RESUME":
            log_alert('resumption')
        elif alert_type == "POSTPONED":
            log_alert('postponement')
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
        venue_name = game['venue']['name']
        roof_type = game['venue']['roof_type']
        
        # Log monitoring with venue info
        if previous_state is None:
            print(f"   🔍 Tracking: {game['matchup']} at {venue_name} ({game['venue']['roof_description']})")
        
        # NEW DELAY DETECTED - Always alert regardless of roof
        if is_weather_delay(game) and previous_state != "DELAYED":
            print(f"🚨 NEW DELAY: {game['matchup']} at {venue_name} - {game['detailed_state']}")
            send_delay_alert(game, "DELAY")
            current_states[game_pk] = {'state': 'DELAYED', 'matchup': game['matchup']}
        
        # GAME RESUMING - Always alert regardless of roof
        elif previous_state == "DELAYED" and current_state == "Live":
            print(f"✅ RESUMING: {game['matchup']} at {venue_name}")
            send_delay_alert(game, "RESUME")
            current_states[game_pk] = {'state': 'LIVE', 'matchup': game['matchup']}
        
        # GAME POSTPONED - Always alert regardless of roof
        elif game['detailed_state'] == 'Postponed' and previous_state != "POSTPONED":
            print(f"📅 POSTPONED: {game['matchup']} at {venue_name}")
            send_delay_alert(game, "POSTPONED")
            current_states[game_pk] = {'state': 'POSTPONED', 'matchup': game['matchup']}
        
        else:
            current_states[game_pk] = {'state': current_state, 'matchup': game['matchup']}
    
    save_game_states(current_states)
    print(f"\n✅ Monitoring complete - checked {len(games)} games")

def main():
    try:
        monitor_games()
        log_workflow_run('success')
    except Exception as e:
        print(f"❌ Error in game status monitor: {e}")
        log_workflow_run('failed')
        raise

if __name__ == "__main__":
    main()
