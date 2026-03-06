def format_game_block(game, weather, impact, recommendations):
    """Format game as Slack block"""
    game_datetime = datetime.strptime(
        f"{game['date']} {game['time']}", 
        "%Y-%m-%d %H:%M"
    )
    
    date_str = game_datetime.strftime("%A, %B %d")
    time_str = game_datetime.strftime("%I:%M %p")
    
    weather_details = (
        f"🌡️ *{weather['temp']:.0f}°F* (feels like {weather['feels_like']:.0f}°F)\n"
        f"☁️ {weather['conditions'].title()}\n"
        f"💧 Rain: *{weather['rain_prob']:.0f}%*\n"
        f"💨 Wind: {weather['wind_speed']:.0f} mph"
    )
    
    if weather['wind_gust'] > weather['wind_speed'] + 5:
        weather_details += f" (gusts to {weather['wind_gust']:.0f} mph)"
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*⚾ {game['opponent']}*\n{date_str} at {time_str}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Weather Forecast:*\n{weather_details}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Game Impact:*\n{impact['emoji']} *{impact['status']}*"
                }
            ]
        }
    ]
    
    if impact['level'] == 'HIGH_RISK':
        blocks.insert(0, {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ *WEATHER ALERT* - High risk of game impact"
            }
        })
    
    return blocks
