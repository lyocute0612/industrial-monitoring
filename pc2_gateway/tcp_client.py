"""TCP client with heartbeat, safe reconnect, and command reception."""
import json
import socket
import threading
import time


class TcpClient:
    def __init__(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.socket = None
        self._send_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._receiver_thread = None
        self._stop_event = threading.Event()
        self._last_ack = 0.0
        self._last_ping = 0.0
        self._last_attempt = 0.0
        self._receiver_callback = None

    def _disconnect(self, sock=None):
        with self._state_lock:
            if sock is not None and self.socket is not sock:
                return
            old = self.socket
            self.socket = None
        if old is not None:
            try:
                old.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                old.close()
            except OSError:
                pass

    def connect(self):
        with self._state_lock:
            if self.socket is not None:
                return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        try:
            sock.connect((self.host, self.port))
            sock.settimeout(1.0)
        except OSError:
            sock.close()
            raise
        with self._state_lock:
            if self.socket is not None:
                sock.close()
                return
            self.socket = sock
            self._last_ack = time.monotonic()
            self._last_ping = 0.0
            self._stop_event.clear()

    def send(self, data: dict):
        payload = (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8")
        with self._send_lock:
            with self._state_lock:
                sock = self.socket
            if sock is None:
                raise ConnectionError("TCP client is not connected")
            try:
                sock.sendall(payload)
            except OSError as error:
                self._disconnect(sock)
                raise ConnectionError(f"TCP send failed: {error}") from error

    def start_receiver(self, on_message):
        self._receiver_callback = on_message
        with self._state_lock:
            sock = self.socket
        if sock is None:
            raise ConnectionError("TCP client is not connected")
        # Each receiver is tied to one socket; a new connection gets a new thread.
        self._receiver_thread = threading.Thread(
            target=self._receive_loop,
            args=(sock, on_message),
            daemon=True,
            name="pc2-command-receiver",
        )
        self._receiver_thread.start()

    def _receive_loop(self, sock, on_message):
        buffer = ""
        while not self._stop_event.is_set():
            with self._state_lock:
                if self.socket is not sock:
                    break
            try:
                data = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not data:
                break
            try:
                buffer += data.decode("utf-8")
            except UnicodeDecodeError:
                break
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError as error:
                    print(f"Invalid JSON from PC1: {error}")
                    continue
                if not isinstance(message, dict):
                    continue
                if message.get("type") == "heartbeat_ack":
                    with self._state_lock:
                        if self.socket is sock:
                            self._last_ack = time.monotonic()
                    continue
                try:
                    on_message(message)
                except Exception as error:
                    print(f"Error while handling PC1 command: {error}")
        self._disconnect(sock)
        print("PC1 command receiver stopped.")

    def maintain(self, on_message=None, reconnect_interval=3.0, heartbeat_interval=2.0, heartbeat_timeout=12.0):
        """Call once per gateway polling cycle; returns whether TCP is connected."""
        if on_message is not None:
            self._receiver_callback = on_message
        now = time.monotonic()
        with self._state_lock:
            sock = self.socket
            last_ack = self._last_ack
            last_ping = self._last_ping
        if sock is not None:
            if now - last_ack > heartbeat_timeout:
                print("WARNING: PC1 heartbeat timeout; reconnecting TCP...")
                self._disconnect(sock)
                return False
            if now - last_ping >= heartbeat_interval:
                try:
                    self.send({"type": "heartbeat"})
                    with self._state_lock:
                        if self.socket is sock:
                            self._last_ping = now
                except ConnectionError as error:
                    print(f"WARNING: {error}")
                    return False
            return True
        if now - self._last_attempt < reconnect_interval:
            return False
        self._last_attempt = now
        try:
            self.connect()
            if self._receiver_callback is not None:
                self.start_receiver(self._receiver_callback)
            print(f"TCP connected to PC1 {self.host}:{self.port}.")
            return True
        except OSError as error:
            print(f"WARNING: TCP reconnect failed: {error}")
            return False

    def close(self):
        self._stop_event.set()
        self._disconnect()
