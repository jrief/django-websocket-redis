
function WS4Redis(options, $) {
	'use strict';
	var opts, ws, deferred, timer, timer_interval = 0;
	var heartbeat_interval = null, missed_heartbeats = 0;

	if (this === undefined)
		return new WS4Redis(options, $);
	if (options.uri === undefined)
		throw new Error('No Websocket URI in options');
	if ($ === undefined)
		$ = jQuery;
	opts = $.extend({ heartbeat_msg: null }, options);
	connect(opts.uri);

	function connect(uri) {
		try {
			console.log("Connecting to " + uri + " ...");
			deferred = $.Deferred();
			ws = new WebSocket(uri);
			ws.onopen = on_open;
			ws.onmessage = on_message;
			ws.onerror = on_error;
			ws.onclose = on_close;
			timer = null;
		} catch (err) {
			deferred.reject(new Error(err));
		}
	}

	function send_heartbeat() {
		try {
			missed_heartbeats++;
			if (missed_heartbeats > 3)
				throw new Error("Too many missed heartbeats.");
			ws.send(opts.heartbeat_msg);
		} catch(e) {
			clearInterval(heartbeat_interval);
			heartbeat_interval = null;
			console.warn("Closing connection. Reason: " + e.message);
			ws.close();
		}
	}

	function on_open() {
		console.log('Connected!');
		timer_interval = 500;
		deferred.resolve();
		if (opts.heartbeat_msg && heartbeat_interval === null) {
			missed_heartbeats = 0;
			heartbeat_interval = setInterval(send_heartbeat, 5000);
		}
	}

	function on_close(evt) {
		console.log("Connection closed!");
		if (!timer) {
			// try to reconnect
			timer = setTimeout(function() {
				connect(ws.url);
			}, timer_interval);
			timer_interval = Math.min(timer_interval + 500, 5000);
		}
	}

	function on_error(evt) {
		console.error("Websocket connection is broken!");
		deferred.reject(new Error(evt));
	}

	function on_message(evt) {
		if (opts.heartbeat_msg && evt.data === opts.heartbeat_msg) {
			// reset the counter for missed heartbeats
			missed_heartbeats = 0;
		} else if (typeof opts.receive_message === 'function') {
			return opts.receive_message(evt.data);
		}
	}

	this.send_message = function(message) {
		ws.send(message);
	}
}
