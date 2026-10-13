from story_finder import messages


def test_owner_facing_copy_is_portuguese_not_english():
    english_giveaways = ["error", "welcome", "please", "sorry", "command"]
    text = " ".join([messages.START, messages.UNEXPECTED_ERROR]).lower()
    assert not any(word in text for word in english_giveaways)


def test_every_public_message_is_a_non_empty_string():
    for name in ["START", "UNEXPECTED_ERROR"]:
        value = getattr(messages, name)
        assert isinstance(value, str) and value.strip()
