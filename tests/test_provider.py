import json

import httpx
import pytest
from openai import OpenAI

from grey_interview.models import Coaching, Config, Evaluation
from grey_interview.provider import Provider, ProviderError


def client_for(payload, requests, status=200):
    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(status, json=payload)

    return OpenAI(
        api_key="test-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )


def response(content, status="completed"):
    return {
        "id": "resp_test",
        "created_at": 1,
        "model": "test-model",
        "object": "response",
        "status": status,
        "output": [
            {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": content,
            }
        ],
    }


@pytest.mark.parametrize("effort", [None, "medium", "high"])
def test_real_sdk_serialization_and_parsing(effort):
    requests = []
    payload = response([{"type": "output_text", "text": '{"reply":"Ready"}', "annotations": []}])
    provider = Provider(Config(provider="openai", effort=effort), client_for(payload, requests))
    result, meta = provider.request("coach", Coaching, {"message": "Hello"})
    assert result == {"reply": "Ready"}
    assert meta["response_id"] == "resp_test"
    assert requests[0]["store"] is False
    if effort:
        assert requests[0]["reasoning"] == {"effort": effort}
    else:
        assert "reasoning" not in requests[0]
    assert requests[0]["text"]["format"]["strict"] is True
    assert requests[0]["text"]["format"]["type"] == "json_schema"
    assert requests[0]["input"][0]["role"] == "system"


@pytest.mark.parametrize(
    "payload",
    [
        response([{"type": "refusal", "refusal": "No"}]),
        response([], "incomplete"),
        response([{"type": "output_text", "text": '{"wrong":3}', "annotations": []}]),
    ],
)
def test_refusal_incomplete_invalid_schema(payload):
    provider = Provider(Config(provider="openai"), client_for(payload, []))
    with pytest.raises(ProviderError):
        provider.request("coach", Coaching, {})


def test_error_body_not_echoed():
    provider = Provider(
        Config(provider="openai"), client_for({"error": {"message": "PRIVATE"}}, [], 401)
    )
    with pytest.raises(ProviderError) as error:
        provider.request("coach", Coaching, {})
    assert "PRIVATE" not in str(error.value)


def test_duplicate_rubric_dimensions_rejected():
    from test_trainer import evaluation

    data = evaluation()
    data["dimensions"][1]["name"] = data["dimensions"][0]["name"]
    payload = response([{"type": "output_text", "text": json.dumps(data), "annotations": []}])
    with pytest.raises(ProviderError, match="dimensions"):
        Provider(Config(provider="openai"), client_for(payload, [])).request(
            "evaluate", Evaluation, {}
        )


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        Provider(Config(provider="openai"))
