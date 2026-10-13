# Catch-up-on-wake scheduling instead of wall-clock

The Digest host is a laptop — it sleeps, closes, and travels — so a wall-clock
schedule would silently skip any week the machine happened to be asleep at the
appointed time, producing no message and no error. Instead of scheduling for a
moment, we check elapsed time: on startup and on an hourly tick, run a Digest if
more than `DIGEST_INTERVAL_DAYS` have passed since the last one and local time falls
inside the send window.

The Digest therefore arrives late rather than never, and the container becomes
restart-safe for free. The send window exists because the naive version of this
design pings the Owner's phone at 3 a.m. the moment the laptop wakes.

## Consequences

The Digest's timing is deliberately imprecise — it fires at the first eligible tick,
not at a fixed hour, and consecutive Digests can be more than seven days apart. That
is the intended trade: a late brief beats a lost one. Anything that needs a
guaranteed fixed-time delivery would need an always-on host, at which point this
decision should be revisited rather than worked around.
