"""All keys share one Redis cluster hash tag; time comes from Redis."""

ADMIT = """
local t = redis.call('TIME')
local now = t[1] * 1000 + math.floor(t[2] / 1000)
local retry = 0
for i = 1, 4 do
  local count = tonumber(redis.call('GET', KEYS[i]) or '0')
  if count > 0 and redis.call('PTTL', KEYS[i]) <= 0 then
    return redis.error_reply('Invalid quota expiry')
  end
  if count >= tonumber(ARGV[i]) then
    retry = math.max(retry, redis.call('PTTL', KEYS[i]))
  end
end
if retry > 0 then return {1, retry} end
redis.call('ZREMRANGEBYSCORE', KEYS[5], '-inf', now)
if redis.call('ZCARD', KEYS[5]) >= tonumber(ARGV[5]) then
  local first = redis.call('ZRANGE', KEYS[5], 0, 0, 'WITHSCORES')
  return {2, math.max(1, tonumber(first[2]) - now)}
end
for i = 1, 4 do
  local count = redis.call('INCR', KEYS[i])
  if count == 1 then
    local ttl = 60000
    if i == 2 or i == 4 then ttl = 86400000 end
    redis.call('PEXPIRE', KEYS[i], ttl)
  end
end
redis.call('ZADD', KEYS[5], now + tonumber(ARGV[6]), ARGV[7])
redis.call('PEXPIRE', KEYS[5], tonumber(ARGV[6]))
return {0, 0}
"""

RELEASE = "return redis.call('ZREM', KEYS[1], ARGV[1])"

RENEW = """
local t = redis.call('TIME')
local now = t[1] * 1000 + math.floor(t[2] / 1000)
local expiry = redis.call('ZSCORE', KEYS[1], ARGV[1])
if not expiry or tonumber(expiry) <= now then return 0 end
redis.call('ZADD', KEYS[1], now + tonumber(ARGV[2]), ARGV[1])
redis.call('PEXPIRE', KEYS[1], tonumber(ARGV[2]))
return 1
"""
