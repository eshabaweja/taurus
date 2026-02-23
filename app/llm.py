import os

def _client():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None


def completion(messages, model="gpt-4o-mini", max_tokens=1024, temperature=0.7, response_format=None):
    """
    Call OpenAI chat completion. Returns content string or None if no client/error.
    """
    client = _client()
    if not client:
        return None
    kwargs = dict(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if response_format is not None:
        kwargs["response_format"] = response_format
    try:
        r = client.chat.completions.create(**kwargs)
        if r.choices and len(r.choices) > 0:
            return (r.choices[0].message.content or "").strip()
    except Exception:
        pass
    return None
