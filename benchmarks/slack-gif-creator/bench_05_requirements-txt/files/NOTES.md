The project sometimes reads source footage with ImageIO's ffmpeg-based backend before turning the frames into a Slack-ready GIF.

Treat that ffmpeg backend as a required runtime dependency, not an optional extra.
