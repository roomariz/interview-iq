"""Deployment-only, atomic limits for the explicitly approved free-provider run."""

import json
import os
import secrets

import httpx
from deployment.phase5_redis import endpoint_url

MODEL = "google/gemma-4-31b-it:free"
ROUTING = {"only": ["google-ai-studio"], "allow_fallbacks": False,
           "max_price": {"prompt": 0, "completion": 0, "request": 0}, "require_parameters": True}
CASE_LIMITS = {"question": 3, "evaluation": 6, "followup": 3}
BASE_SEND = httpx.Client.send

SCRIPT = """
local run, rate, events = KEYS[1], KEYS[2], KEYS[3]
local t = redis.call('TIME')
local now = tonumber(t[1])*1000 + math.floor(tonumber(t[2])/1000)
local action, group, owner = ARGV[1], ARGV[2], ARGV[3]
if action == 'close' then redis.call('HSET',run,'open',0); return 1 end
if redis.call('HGET',run,'open') ~= '1' or
  now >= tonumber(redis.call('HGET',run,'expires_ms') or '0') then return -1 end
if action == 'workflow' then
  if redis.call('HGET',run,'phase') ~= group or redis.call('HEXISTS',run,'used:'..group)==1 or
    tonumber(redis.call('HGET',run,'workflows') or '0') >= 3 then return -2 end
  redis.call('HSET',run,'used:'..group,1,'owner',owner)
  redis.call('HINCRBY',run,'workflows',1)
  return 1
end
if redis.call('HGET',run,'owner') ~= owner or redis.call('HGET',run,'phase') ~= group then return -3 end
if action == 'reserve' then
  local ceiling = ({question=3,evaluation=6,followup=3})[group]
  if not ceiling or redis.call('HEXISTS',run,'active')==1 or
    tonumber(redis.call('HGET',run,'attempts') or '0') >= 12 or
    tonumber(redis.call('HGET',run,'attempts:'..group) or '0') >= ceiling then return -4 end
  redis.call('ZREMRANGEBYSCORE',rate,'-inf',now-60000)
  if redis.call('ZCARD',rate)>=10 then return -5 end
  local count = redis.call('HINCRBY',run,'attempts',1)
  redis.call('HINCRBY',run,'attempts:'..group,1)
  redis.call('HINCRBY',run,'reserved_input',16384)
  redis.call('HINCRBY',run,'reserved_output',2048)
  redis.call('HSET',run,'active',ARGV[4])
  redis.call('ZADD',rate,now,ARGV[4])
  redis.call('EXPIRE',rate,86400)
  redis.call('RPUSH',events,cjson.encode({event='reserved',case=group,attempt=count,at_ms=now}))
  redis.call('EXPIRE',events,86400)
  return count
end
if action == 'finish' then
  if redis.call('HGET',run,'active') ~= ARGV[4] then return -6 end
  redis.call('RPUSH',events,ARGV[5])
  redis.call('HDEL',run,'active')
  return 1
end
return -7
"""


def command(*parts):
    """Use the original send method, restricted to the configured Redis origin."""
    url = endpoint_url()
    with httpx.Client(timeout=5, trust_env=False, follow_redirects=False) as client:
        request = client.build_request("POST", url, json=list(parts), headers={
            "Authorization": "Bearer " + os.environ["UPSTASH_REDIS_REST_TOKEN"]})
        response = BASE_SEND(client, request, follow_redirects=False)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError("Phase 5 Redis failure")
        return payload["result"]


def keys():
    run = os.environ["PHASE5_RUN_ID"]
    if not run.isalnum() or len(run) < 16:
        raise RuntimeError("Invalid Phase 5 identity")
    root = "{interviewiq-mocked-preview}:phase5:" + run
    return [root, root + ":rate", root + ":events"]


def action(name, group="", owner="", attempt="", event=None):
    result = command("EVAL", SCRIPT, 3, *keys(), name, group, owner, attempt,
                     json.dumps(event or {}, separators=(",", ":")))
    if type(result) is not int or result < 1:
        raise RuntimeError("Phase 5 control denied")
    return result


def workflow(group):
    owner = secrets.token_hex(24)
    action("workflow", group, owner)
    return owner


def reserve(group, owner):
    attempt = secrets.token_hex(24)
    number = action("reserve", group, owner, attempt)
    return attempt, number
