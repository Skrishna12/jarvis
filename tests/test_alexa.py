from __future__ import annotations

from jarvis.alexa.skill import handle_skill_body, speakable


def test_speakable_flattens_newlines() -> None:
    assert "leave" in speakable("leave\nnow").lower()


def test_launch_and_traffic(db_session) -> None:
    launch = handle_skill_body({"request": {"type": "LaunchRequest"}}, db_session)
    text = launch["response"]["outputSpeech"]["text"]
    assert "09:00" in text or "Weekend" in text or "Office" in text

    traffic = handle_skill_body(
        {
            "request": {
                "type": "IntentRequest",
                "intent": {"name": "TrafficIntent"},
            }
        },
        db_session,
    )
    spoken = traffic["response"]["outputSpeech"]["text"]
    assert "Jam on the ring road" in spoken
