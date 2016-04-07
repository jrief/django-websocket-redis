/**
 * options.uri - > The Websocket URI
 * options.connected -> Callback called after the websocket is connected.
 * options.connecting -> Callback called when the websocket is connecting.
 * options.disconnected -> Callback called after the websocket is disconnected.
 * options.receive_message -> Callback called when a message is received from the websocket.
 * options.heartbeat_msg -> String to identify the heartbeat message.
 * $ -> JQuery instance.
 */
function WS4Redis(options, $) {
	'use strict';
	var opts, ws, deferred, timer, attempts = 1, must_reconnect = true;
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
			if (ws && (is_connecting() || is_connected())) {
				console.log("Websocket is connecting or already connected.");
				return;
			}
			
			if ($.type(opts.connecting) === 'function') {
				opts.connecting();
			}
			
			console.log("Connecting to " + uri + " ...");
			deferred = $.Deferred();
			ws = new WebSocket(uri);
			ws.onopen = on_open;
			ws.onmessage = on_message;
			ws.onerror = on_error;
			ws.onclose = on_close;
			timer = null;
		} catch (err) {
			try_to_reconnect();
			deferred.reject(new Error(err));
		}
	}

	function try_to_reconnect() {
		if (must_reconnect && !timer) {
			// try to reconnect
			console.log('Reconnecting...');
			var interval = generate_inteval(attempts);
			timer = setTimeout(function() {
				attempts++;
				connect(ws.url);
			}, interval);
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
			if ( !is_closing() && !is_closed() ) {
				ws.close();
			}
		}
	}

	function on_open() {
		console.log('Connected!');
		// new connection, reset attemps counter
		attempts = 1;
		deferred.resolve();
		if (opts.heartbeat_msg && heartbeat_interval === null) {
			missed_heartbeats = 0;
			heartbeat_interval = setInterval(send_heartbeat, 5000);
		}
		if ($.type(opts.connected) === 'function') {
			opts.connected();
		}
	}

	function on_close(evt) {
		console.log("Connection closed!");
		if ($.type(opts.disconnected) === 'function') {
			opts.disconnected(evt);
		}
		try_to_reconnect();
	}

	function on_error(evt) {
		console.error("Websocket connection is broken!");
		deferred.reject(new Error(evt));
	}

	function on_message(evt) {
		if (opts.heartbeat_msg && evt.data === opts.heartbeat_msg) {
			// reset the counter for missed heartbeats
			missed_heartbeats = 0;
		} else if ($.type(opts.receive_message) === 'function') {
			return opts.receive_message(evt.data);
		}
	}

	// this code is borrowed from http://blog.johnryding.com/post/78544969349/
	//
	// Generate an interval that is randomly between 0 and 2^k - 1, where k is
	// the number of connection attmpts, with a maximum interval of 30 seconds,
	// so it starts at 0 - 1 seconds and maxes out at 0 - 30 seconds
	function generate_inteval(k) {
		var maxInterval = (Math.pow(2, k) - 1) * 1000;

		// If the generated interval is more than 30 seconds, truncate it down to 30 seconds.
		if (maxInterval > 30*1000) {
			maxInterval = 30*1000;
		}

		// generate the interval to a random number between 0 and the maxInterval determined from above
		return Math.random() * maxInterval;
	}

	this.send_message = function(message) {
		ws.send(message);
	};
	
	this.get_state = function() {
		return ws.readyState;	
	};
	
	function is_connecting() {
		return ws && ws.readyState === 0;	
	}
	
	function is_connected() {
		return ws && ws.readyState === 1;	
	}
	
	function is_closing() {
		return ws && ws.readyState === 2;	
	}

	function is_closed() {
		return ws && ws.readyState === 3;	
	}
	
	
	this.close = function () {
		clearInterval(heartbeat_interval);
		must_reconnect = false;
		if (!is_closing() || !is_closed()) {
			ws.close();
		}
	}
	
	this.is_connecting = is_connecting; 
	this.is_connected = is_connected;
	this.is_closing = is_closing;
	this.is_closed = is_closed;
}
