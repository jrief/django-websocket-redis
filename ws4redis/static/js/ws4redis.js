(function() {
"use strict";

/**
 * options.uri - > The Websocket URI
 * options.connected -> Callback called after the websocket is connected.
 * options.connecting -> Callback called when the websocket is connecting.
 * options.disconnected -> Callback called after the websocket is disconnected.
 * options.receive_message -> Callback called when a message is received from the websocket.
 * options.heartbeat_msg -> String to identify the heartbeat message.
 * $ -> JQuery instance.
 */
var WS4Redis = function (options, $) {
	
	if (!(this instanceof WS4Redis)) {
		// Trick to ensure that WS4Redis is always instantiated.
		return new WS4Redis(options, $);
	}
	
	this.ws = null;
	this.deferred = null
	this.timer = null;
	this.attempts = 1;
	this.must_reconnect = true;
	this.heartbeat_interval = null
	this.missed_heartbeats = 0;

	if (options.uri === undefined)
		throw new Error('No Websocket URI in options');
	
	if ($ === undefined)
		this.$ = jQuery;
	else
		this.$ = $;
	
	this.opts = this.$.extend({ heartbeat_msg: null }, options);
	this.connect(this.opts.uri);
}

WS4Redis.prototype.connect = function(uri) {
	try {
		if (this.ws && (this.is_connecting() || this.is_connected())) {
			console.log("Websocket is connecting or already connected.");
			return;
		}
		
		if (this.$.type(this.opts.connecting) === 'function') {
			this.opts.connecting();
		}
		
		console.log("Connecting to " + uri + " ...");
		this.timer = null;
		this.deferred = this.$.Deferred();
		this.ws = new WebSocket(uri);
		var binder = this;
		this.ws.onopen = function () { binder._on_open(); };
		this.ws.onmessage = function (evt) { binder._on_message(evt); };
		this.ws.onclose = function (evt) { binder._on_close(evt); };
		this.ws.onerror = function (evt) { binder._on_error(evt); };
	} catch (err) {
		this._try_to_reconnect();
		this.deferred.reject(new Error(err));
	}
}

WS4Redis.prototype.send_heartbeat = function () {
	try {
		this.missed_heartbeats++;
		if (this.missed_heartbeats > 3) {
			throw new Error("Too many missed heartbeats.");
		}
		this.ws.send(this.opts.heartbeat_msg);
	} catch(e) {
		clearInterval(this.heartbeat_interval);
		this.heartbeat_interval = null;
		console.warn("Closing connection. Reason: " + e.message);
		this.ws.close();
	}
}

WS4Redis.prototype._on_open = function() {
	console.log('Connected!');
	// new connection, reset attemps counter
	var binder = this;
	this.attempts = 1;
	this.deferred.resolve();
	if (this.opts.heartbeat_msg && this.heartbeat_interval === null) {
		this.missed_heartbeats = 0;
		this.heartbeat_interval = setInterval(function(){binder.send_heartbeat();}, 5000);
	}
	if (this.$.type(this.opts.connected) === 'function') {
		this.opts.connected();
	}
}

WS4Redis.prototype._on_close = function (evt) {
	console.log("Connection closed!");
	
	if (this.$.type(this.opts.disconnected) === 'function') {
		this.opts.disconnected(evt);
	}
	
	this._try_to_reconnect();
}

WS4Redis.prototype._try_to_reconnect = function () {
	if (this.must_reconnect && !this.timer) {
		// try to reconnect
		console.log('Reconnecting...');
		var interval = this._generate_inteval(this.attempts);
		var binder = this;
		this.timer = setTimeout(function() {
			binder.attempts++;
			binder.connect(binder.ws.url);
		}, interval);
	}
}

WS4Redis.prototype._on_error = function (evt) {
	console.error("Websocket connection is broken!");
	this.deferred.reject(new Error(evt));
}

WS4Redis.prototype._on_message = function (evt) {
	if (this.opts.heartbeat_msg && evt.data === this.opts.heartbeat_msg) {
		// reset the counter for missed heartbeats
		this.missed_heartbeats = 0;
	} else if (this.$.type(this.opts.receive_message) === 'function') {
		return this.opts.receive_message(evt.data);
	}
}

// this code is borrowed from http://blog.johnryding.com/post/78544969349/
// Generate an interval that is randomly between 0 and 2^k - 1, where k is
// the number of connection attmpts, with a maximum interval of 30 seconds,
// so it starts at 0 - 1 seconds and maxes out at 0 - 30 seconds
WS4Redis.prototype._generate_inteval = function (k) {
	var maxInterval = (Math.pow(2, k) - 1) * 1000;

	// If the generated interval is more than 30 seconds, truncate it down to 30 seconds.
	if (maxInterval > 30*1000) {
		maxInterval = 30*1000;
	}

	// generate the interval to a random number between 0 and the maxInterval determined from above
	return Math.random() * maxInterval;
}

WS4Redis.prototype.send_message = function(message) {
	this.ws.send(message);
}

WS4Redis.prototype.is_connecting = function() {
	return this.ws.readyState == 0;	
}

WS4Redis.prototype.is_connected = function() {
	return this.ws.readyState == 1;	
}

WS4Redis.prototype.is_closing = function() {
	return this.ws.readyState == 2;	
}

WS4Redis.prototype.is_closed = function() {
	return this.ws.readyState == 3;	
}

WS4Redis.prototype.get_state = function() {
	return this.ws.readyState;	
}

WS4Redis.prototype.close = function () {
	clearInterval(this.heartbeat_interval);
	this.must_reconnect = false;
	if (!this.is_closing() || !this.is_closed()) {
		this.ws.close();
	}
}

window.WS4Redis = WS4Redis

})();
