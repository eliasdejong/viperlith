local function envs(k, d)
	local v = os.getenv(k)
	return (v == nil or v == "") and d or v
end

local function envn(k, d)
	local v = os.getenv(k)
	if v == nil or v == "" then return d end
	v = tonumber(v)
	assert(v ~= nil, k .. " must be numeric")
	return v
end

local function zipf_rank(count, alpha)
	local u = math.random()
	local p = 1.0 - alpha
	local rank = (1.0 + u * (count ^ p - 1.0)) ^ (1.0 / p)
	return math.max(1, math.min(count, math.floor(rank + 0.5)))
end

local C = {
	read_pct = envn("BENCH_READ_PCT", 100),
	bench_skew = envn("BENCH_SKEW", 0.1), -- Controls how concentrated message writes are over logical channels.

	msg_size_min = envn("WRK_MESSAGE_SIZE_MIN", 1),
	msg_size_max = envn("WRK_MESSAGE_SIZE_MAX", 127),

	seed_channel_count = tonumber(os.getenv("SEED_CHANNEL_COUNT")),
	seed_user_count = tonumber(os.getenv("SEED_USER_COUNT")),
	seed_msg_count = tonumber(os.getenv("SEED_MSG_COUNT")),
}

function init()
	math.randomseed(os.time() + tonumber(tostring({}):match("0x(%x+)"), 16))
end

local fmt, random, rep = string.format, math.random, string.rep

local GET_HEADERS = {
	["Datastar-Request"] = "true",
	["Accept"] = "text/html, application/json",
	["Accept-Encoding"] = "br",
}

local POST_HEADERS = {
	["Datastar-Request"] = "true",
	["Content-Type"] = "application/json",
	["Accept"] = "text/html, application/json",
	["Accept-Encoding"] = "br",
}

function request()
	local is_read = random(100) <= C.read_pct
	if is_read then
		return wrk.format("GET", "/", GET_HEADERS)
	else
		local url
		local signals
		local roll = random(100)
		if roll <= 80 then
			local msg_size = random(C.msg_size_min, C.msg_size_max)
			url = "/chat/message-send"
			signals = '{"messageSend":"' .. rep("a", msg_size) .. '"}'
		elseif roll <= 90 then
			url = "/chat/channel-open"
			signals = '{"channelOpen":"' .. fmt("c_%08d", zipf_rank(C.seed_channel_count, C.bench_skew)) .. '"}'
		else
			url = "/chat/nickname-set"
			signals = '{"nicknameSet":"' .. fmt("u_%08d", random(C.seed_user_count)) .. '"}'
		end
		return wrk.format("POST", url, POST_HEADERS, signals)
	end
end