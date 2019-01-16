/**
  * options & defaults
    - maxAttempts: 50,
    - mustReconnect: true,
    - uri: null,
    - heartbeatMsg: null,
    - maxMissedHeartbeats: 5,
    - heartbeatLapse: 5000,
    - autoConnect: true,
    - receiveMessage (notification, evt) {
        console.log('ws4redis receive message', evt)
      },
    - connecting () {
        console.log('ws4redis connecting...')
      },
    - connected () {
        console.log('ws4redis connected')
      },
    - reconnecting (attempts, time, e) {
        console.log('ws4redis Reconnect attept ' + attempts + ' on ' + time, e)
      },
    - error (evt) {
        console.error('ws4redis error', evt)
      },
    - heartbeatTimeout (e) {
        console.error('ws4redis heartbeat timeot, closing', e)
      },
    - disconnected (evt) {
        console.error('disconnected', evt)
      }
*/

const generateInteval = function (k) {
  const max = 30 * 1000
  const interval = (Math.pow(2, k) - 1) * 1000
  return interval > max ? max : interval // Math.random() * <- for randomly factor
}

class WS4Redis {
  constructor (options) {
    // Retrofix options params:
    if (options.receive_message) {
      options.receiveMessage = options.receive_message
      delete options.receive_message
    }
    if (options.heartbeat_msg) {
      options.heartbeatMsg = options.heartbeat_msg
      delete options.heartbeat_msg
    }

    const self = this
    self.options = Object.assign({
      maxAttempts: 50,
      mustReconnect: true,
      uri: null,
      heartbeatMsg: null,
      maxMissedHeartbeats: 5,
      heartbeatLapse: 5000,
      autoConnect: true,
      receiveMessage (notification, evt) {
        console.log('ws4redis receive message', evt)
      },
      connecting () {
        console.log('ws4redis connecting...')
      },
      connected () {
        console.log('ws4redis connected')
      },
      reconnecting (attempts, time, e) {
        console.log('ws4redis Reconnect attept ' + attempts + ' on ' + time, e)
      },
      error (evt) {
        console.error('ws4redis error', evt)
      },
      heartbeatTimeout (e) {
        console.error('ws4redis heartbeat timeot, closing', e)
      },
      disconnected (evt) {
        console.error('disconnected', evt)
      }
    }, options)
    self.attempts = 0
    self.ws = null
    self.timer = null
    self.heartbeatInterval = null
    self.missedHeartbeats = 0
    self.forcedClose = false

    if (!self.options.uri) { throw new Error('No Websocket URI in options') }

    if (self.options.autoConnect) {
      self.connect()
    }
  }

  connect () {
    const self = this
    try {
      if (self.ws && (self.isConnecting() || self.isConnected())) {
        console.warn('Websocket is connecting or already connected.')
        return
      }

      if (typeof self.options.connecting === 'function') {
        self.options.connecting()
      }

      const ws = new WebSocket(self.options.uri)
      ws.onopen = function () {
        self.attempts = 1

        if (self.options.heartbeatMsg && self.heartbeatInterval === null) {
          self.missedHeartbeats = 0
          self.heartbeatInterval = setInterval(function () {
            self.sendHeartbeat()
          }, self.options.heartbeatLapse)
        }
        if (typeof self.options.connected === 'function') {
          self.options.connected()
        }
      }
      ws.onmessage = function (evt) {
        if (self.options.heartbeatMsg && evt.data === self.options.heartbeatMsg) {
          self.missedHeartbeats = 0
        } else if (typeof self.options.receiveMessage === 'function') {
          return self.options.receiveMessage(evt.data, evt)
        }
      }
      ws.onerror = function (evt) {
        if (typeof self.options.error === 'function') {
          self.options.error(evt)
        }
      }
      ws.onclose = function (evt) {
        if (self.heartbeatInterval) {
          clearInterval(self.heartbeatInterval)
          self.heartbeatInterval = null
        }
        if (typeof self.options.disconnected === 'function') {
          self.options.disconnected(evt)
        }
        if (!self.forcedClose) {
          self.forcedClose = false
          self.reconnect()
        }
      }
      self.ws = ws
      self.timer = null
    } catch (e) {
      self.reconnect(e)
    }
  }

  reconnect (e) {
    const self = this
    if (self.options.mustReconnect && !self.timer && self.attempts < self.options.maxAttempts) {
      const time = generateInteval(self.attempts)
      if (typeof self.options.reconnecting === 'function') {
        self.options.reconnecting(self.attempts, time, e)
      }
      self.timer = setTimeout(function () {
        self.attempts++
        self.connect()
      }, time)
    }
  }

  close () {
    const self = this
    self.forcedClose = true
    if (!self.isClosing() || !self.isClosed()) {
      self.ws.close()
    }
  }

  sendHeartbeat () {
    const self = this
    try {
      self.missedHeartbeats++
      if (self.missedHeartbeats >= self.options.maxMissedHeartbeats) { throw new Error('Too many missed heartbeats.') }
      self.ws.send(self.options.heartbeatMsg)
    } catch (e) {
      if (typeof self.options.heartbeatTimeout === 'function') {
        self.options.heartbeatTimeout(e)
      }
      if (!self.isClosing() && !self.isClosed()) {
        self.ws.close()
      }
    }
  }

  sendMessage (message) {
    this.ws.send(message)
  }

  getState () {
    return this.ws.readyState
  }

  isConnecting () {
    return this.ws && this.ws.readyState === 0
  }

  isConnected () {
    return this.ws && this.ws.readyState === 1
  }

  isClosing () {
    return this.ws && this.ws.readyState === 2
  }

  isClosed () {
    return this.ws && this.ws.readyState === 3
  }
}
