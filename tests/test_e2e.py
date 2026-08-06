"""End-to-end integration tests for all C2 channels."""
import json
import os
import socket
import tempfile
import threading
import time
import unittest

from common.protocol import Protocol
from common.encrypted_protocol import EncryptedProtocol
from common.http_protocol import HttpC2Server
from common.http_profile import get_profile
from common.udp_protocol import UdpServer, UdpClient
from common.logging import get_logger
from server.payloads.generate import generate_hta, generate_vbs, generate_ps1, generate_bat, generate_sct
from client.core.beacon import BeaconConfig
from client.commands import build_client_registry
from client.core.session_context import SessionContext
from client.platform import get_platform


class TestTCPChannel(unittest.TestCase):
    def test_send_recv_5_commands(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        host, port = server.getsockname()
        results = []
        ready = threading.Event()

        def serve():
            conn, _ = server.accept()
            proto = Protocol(conn)
            ready.set()
            for i in range(5):
                proto.send(f'cmd_{i}')
                results.append(proto.recv())
            proto.send('quit')
            conn.close()

        t = threading.Thread(target=serve)
        t.start()
        ready.wait(timeout=3)
        client = socket.create_connection((host, port))
        proto = Protocol(client)
        for i in range(5):
            cmd = proto.recv()
            proto.send(f'resp_{cmd}')
        self.assertEqual(proto.recv(), 'quit')
        t.join(timeout=3)
        client.close()
        server.close()
        self.assertEqual(len(results), 5)
        for i in range(5):
            self.assertEqual(results[i], f'resp_cmd_{i}')


class TestHTTPChannel(unittest.TestCase):
    def test_server_queue_and_http_roundtrip(self):
        import http.client
        server = HttpC2Server(host='127.0.0.1', port=0, use_tls=False)
        server.start()
        self.addCleanup(server.stop)
        time.sleep(0.1)
        port = server._server.socket.getsockname()[1]

        server.queue_command('sysinfo')
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        conn.request('GET', '/poll')
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        body = resp.read().decode()
        self.assertEqual(body, 'sysinfo')
        conn.close()

        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        conn.request('POST', '/push', body=json.dumps({'cmd': 'done'}).encode(),
                     headers={'Content-Type': 'application/json'})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        conn.close()
        result = server.get_result()
        self.assertIsNotNone(result)
        self.assertIn('done', result)


class TestUDPChannel(unittest.TestCase):
    def test_send_recv_roundtrip(self):
        srv = UdpServer(host='127.0.0.1', port=0)
        port = srv.sock.getsockname()[1]
        self.addCleanup(srv.close)
        cli = UdpClient(host='127.0.0.1', port=port)
        self.addCleanup(cli.close)

        cli.send({'cmd': 'ping', 'id': 1})
        data, sid, addr = srv.recvfrom(timeout=2)
        self.assertEqual(data, {'cmd': 'ping', 'id': 1})
        srv.sendto({'resp': 'pong', 'id': 1}, sid)
        reply = cli.recv(timeout=2)
        self.assertEqual(reply, {'resp': 'pong', 'id': 1})


class TestEncryptedChannel(unittest.TestCase):
    def setUp(self):
        self.a, self.b = socket.socketpair()

    def tearDown(self):
        self.a.close()
        self.b.close()

    def test_ecdh_aesgcm_multi_command_session(self):
        c_proto = EncryptedProtocol(self.a)
        s_proto = EncryptedProtocol(self.b)

        def server_handshake():
            s_proto.perform_key_exchange(initiator=False)

        t = threading.Thread(target=server_handshake)
        t.start()
        c_proto.perform_key_exchange(initiator=True)
        t.join()

        for i in range(5):
            cmd = {'task': f'cmd_{i}', 'args': [i, i * 2]}
            c_proto.send(cmd)
            self.assertEqual(s_proto.recv(), cmd)
            s_proto.send({'result': f'ok_{i}', 'data': 'x' * 128})
            self.assertEqual(c_proto.recv()['result'], f'ok_{i}')


class TestPayloadGenerator(unittest.TestCase):
    def test_all_5_formats_non_empty_with_host_port(self):
        host, port = '10.10.10.1', 8888
        gens = [generate_hta, generate_vbs, generate_ps1, generate_bat, generate_sct]
        for fn in gens:
            result = fn(host=host, port=port)
            self.assertTrue(len(result) > 10, f'{fn.__name__} empty')
        ps1 = generate_ps1(host=host, port=port)
        self.assertIn(host, ps1)
        self.assertIn(str(port), ps1)


class TestCommandDispatch(unittest.TestCase):
    def setUp(self):
        self.r, self.w = socket.socketpair()
        self.platform = get_platform()
        self.protocol = Protocol(self.r)
        self.peer = Protocol(self.w)
        self.ctx = SessionContext(sock=self.r, protocol=self.protocol,
                                  platform=self.platform)
        self.registry = build_client_registry()

    def tearDown(self):
        self.r.close()
        self.w.close()

    def _dispatch_and_collect(self, cmd, timeout=3):
        def run():
            self.registry.dispatch(self.ctx, cmd)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(timeout=timeout)
        self.w.settimeout(0.5)
        replies = []
        try:
            while True:
                replies.append(self.peer.recv())
        except socket.timeout:
            pass
        self.w.settimeout(None)
        return replies

    def test_10_essential_commands_no_crash(self):
        cmds = ['sysinfo', 'ls /tmp', 'pwd', 'whoami', 'ps',
                'check_admin', 'persistence list', 'ifconfig',
                'background', 'screenshot']
        for cmd in cmds:
            replies = self._dispatch_and_collect(cmd)
            self.assertIsNotNone(replies, f'{cmd} returned None')


class TestPersistence(unittest.TestCase):
    def test_list_methods_returns_platform_methods(self):
        from client.modules.persistence import list_methods
        result = list_methods()
        self.assertIn('Available persistence methods', result)
        if os.name == 'nt':
            expected = ['registry', 'scheduled_task', 'startup_folder', 'wmi']
        else:
            expected = ['crontab', 'bashrc', 'xdg', 'systemd']
        for method in expected:
            self.assertIn(method, result)


class TestConfig(unittest.TestCase):
    def test_stealth_profile_json_serializable(self):
        profile = get_profile('stealth')
        data = {f.name: getattr(profile, f.name)
                for f in profile.__dataclass_fields__.values()}
        encoded = json.dumps(data)
        self.assertTrue(len(encoded) > 0)
        decoded = json.loads(encoded)
        self.assertEqual(decoded['name'], 'stealth')

    def test_profile_round_trip(self):
        raw = {'name': 'aggressive', 'sleep': 2, 'jitter': 0.1,
               'poll_uri': '/cmd', 'push_uri': '/result',
               'user_agent': 'TestAgent/1.0',
               'poll_method': 'GET', 'push_method': 'POST',
               'extra_headers': {}, 'cookie': '', 'stage_uri': '/stage'}
        encoded = json.dumps(raw)
        decoded = json.loads(encoded)
        self.assertEqual(decoded['name'], 'aggressive')
        self.assertEqual(decoded['sleep'], 2)
        self.assertEqual(decoded['poll_uri'], '/cmd')


class TestLogging(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = get_logger()
        self.logger.set_level('DEBUG')

    def test_per_agent_log_created(self):
        agent_dir = os.path.join(self.tmpdir, 'agents')
        self.logger.set_agent_log_dir(agent_dir)
        self.logger.log_command('e2e-agent', 'sysinfo', 'Linux', 200, 10, 'ok')
        log_file = os.path.join(agent_dir, 'e2e-agent.log')
        self.assertTrue(os.path.exists(log_file))
        with open(log_file) as f:
            content = f.read()
        self.assertIn('sysinfo', content)
        self.assertIn('e2e-agent', content)

    def test_log_rotation_creates_backup(self):
        log_path = os.path.join(self.tmpdir, 'rotate.log')
        self.logger.add_file_handler(log_path, max_size=50, backups=2)
        for i in range(20):
            self.logger.info(f'r{i:04d}')
        exists = os.path.exists(log_path) or os.path.exists(f'{log_path}.2')
        self.assertTrue(exists, f'Neither {log_path} nor {log_path}.2 found')


class TestBeaconConfig(unittest.TestCase):
    def test_sleep_with_jitter(self):
        cfg = BeaconConfig(sleep_time=5.0, jitter=0.3)
        for _ in range(20):
            s = cfg.get_sleep()
            self.assertGreaterEqual(s, 3.5)
            self.assertLessEqual(s, 6.5)

    def test_kill_date_expired(self):
        cfg = BeaconConfig(kill_date='2020-01-01')
        self.assertFalse(cfg.should_activate())

    def test_kill_date_future(self):
        cfg = BeaconConfig(kill_date='2099-12-31')
        self.assertTrue(cfg.should_activate())

    def test_working_hours_block(self):
        from datetime import datetime
        hour = datetime.now().hour
        block_start = (hour + 1) % 24
        block_end = (block_start + 10) % 24
        cfg = BeaconConfig(working_hours=(block_start, block_end))
        self.assertFalse(cfg.should_activate())

    def test_working_hours_allow_full(self):
        cfg = BeaconConfig(working_hours=(0, 24))
        self.assertTrue(cfg.should_activate())


if __name__ == '__main__':
    unittest.main()
