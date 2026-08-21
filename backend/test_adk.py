import sys
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import InMemoryRunner

from agents.test_agent import root_agent

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

runner = InMemoryRunner(agent=root_agent)

session = runner.session_service.create_session_sync(
    app_name=runner.app_name,
    user_id="test_user"
)

message = types.Content(
    role="user",
    parts=[types.Part(text="What is a mutual fund?")]
)

for event in runner.run(
    user_id="test_user",
    session_id=session.id,
    new_message=message
):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                print(part.text)
