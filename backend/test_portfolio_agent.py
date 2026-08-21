import sys
from google.genai import types
from google.adk.runners import InMemoryRunner

from agents.portfolio_agent import portfolio_agent

sys.stdout.reconfigure(encoding="utf-8")

runner = InMemoryRunner(agent=portfolio_agent)

session = runner.session_service.create_session_sync(
    app_name=runner.app_name,
    user_id="test_user"
)

message = types.Content(
    role="user",
    parts=[types.Part(text="What stocks are in portfolio 1?")]
)

tool_called = False
final_text = None

for event in runner.run(
    user_id="test_user",
    session_id=session.id,
    new_message=message
):
    if not event.content or not event.content.parts:
        continue

    for part in event.content.parts:

        if part.function_call:
            tool_called = True
            print(f"[TOOL CALL] {part.function_call.name}({dict(part.function_call.args)})")

        if part.function_response:
            print(f"[TOOL RESULT] {part.function_response.name} -> {part.function_response.response}")

        if part.text:
            final_text = part.text

print()
print("=== Success criteria ===")
print("Tool was called:", tool_called)
print()
print("=== Final answer ===")
print(final_text)
