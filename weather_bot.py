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
