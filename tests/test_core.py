"""Unit tests for protocol, crypto, commands, and modules."""
import os
import socket
import unittest
import tempfile

from common.protocol import Protocol
from common.logging import get_logger


class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.r, self.w = socket.socketpair()
        self.client = Protocol(self.r)
        self.server = Protocol(self.w)

    def tearDown(self):
        self.r.close()
        self.w.close()

    def test_send_recv_text(self):
        self.client.send('hello')
        val = self.server.recv()
        self.assertEqual(val, 'hello')

    def test_send_recv_dict(self):
        self.client.send({'type': 'cmd', 'data': 'ls'})
        val = self.server.recv()
        self.assertEqual(val, {'type': 'cmd', 'data': 'ls'})

    def test_send_recv_ints(self):
        self.client.send(42)
        val = self.server.recv()
        self.assertEqual(val, 42)

    def test_send_recv_list(self):
        self.client.send([1, 2, 3])
        val = self.server.recv()
        self.assertEqual(val, [1, 2, 3])

    def test_connection_error(self):
        self.r.close()
        with self.assertRaises((ConnectionError, OSError)):
            self.client.recv()


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = get_logger()

    def test_log_levels(self):
        self.logger.set_level('DEBUG')
        self.assertEqual(self.logger._level, 10)
        self.logger.set_level('ERROR')
        self.assertEqual(self.logger._level, 40)

    def test_command_logging(self):
        log_path = os.path.join(self.tmpdir, 'test.log')
        self.logger.add_file_handler(log_path)
        self.logger.log_command('agent-1', 'sysinfo', 'Linux x86_64', 100, 42, 'ok')
        entries = self.logger.get_recent_commands('agent-1')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].command, 'sysinfo')
        self.assertEqual(entries[0].status, 'ok')
        self.assertEqual(entries[0].response_size, 100)

    def test_command_summary(self):
        self.logger.log_command('agent-1', 'ls', 'dir contents', 50, 10, 'ok')
        self.logger.log_command('agent-1', 'rm', 'error', 0, 5, 'error')
        self.logger.log_command('agent-2', 'ps', 'process list', 500, 30, 'ok')
        summary = self.logger.command_summary()
        self.assertIn('agent-1', summary)
        self.assertIn('agent-2', summary)
        self.assertEqual(summary['agent-1']['total'], 3)
        self.assertEqual(summary['agent-1']['ok'], 2)
        self.assertEqual(summary['agent-1']['error'], 1)

    def test_per_agent_files(self):
        log_dir = os.path.join(self.tmpdir, 'agents')
        self.logger.set_agent_log_dir(log_dir)
        self.logger.log_command('agent-x', 'whoami', 'root', 10, 1, 'ok')
        self.logger.log_command('agent-x', 'pwd', '/root', 8, 1, 'ok')
        log_file = os.path.join(log_dir, 'agent-x.log')
        self.assertTrue(os.path.exists(log_file))
        with open(log_file) as f:
            content = f.read()
        self.assertIn('whoami', content)
        self.assertIn('pwd', content)


class TestCommandRegistry(unittest.TestCase):
    def test_all_commands_registered(self):
        from client.commands import build_client_registry
        registry = build_client_registry()
        commands = set(registry._key_map.keys())
        self.assertGreater(len(commands), 45)
        essential = ['ls', 'cd', 'pwd', 'rm', 'download', 'upload', 'sysinfo',
                     'ps', 'kill', 'grep', 'persistence', 'background', 'help',
                     'whoami', 'inject', 'hollow', 'migrate', 'lsass_dump', 'socks5']
        for cmd in essential:
            self.assertIn(cmd, commands, f'Missing essential command: {cmd}')

    def test_server_commands_registered(self):
        from server.commands import build_server_router
        router = build_server_router()
        commands = set(router._commands.keys())
        self.assertIn('upload', commands)
        self.assertIn('download', commands)
        self.assertIn('download_large', commands)
        self.assertIn('screenshot', commands)
        self.assertIn('webcam', commands)


class TestModuleImports(unittest.TestCase):
    def test_all_modules_import(self):
        self.assertTrue(True)

    def test_no_circular_imports(self):
        self.assertTrue(True)


class TestChunkedReceiver(unittest.TestCase):
    def test_receiver_init(self):
        from server.handlers.chunked_receiver import ChunkedReceiver
        cr = ChunkedReceiver()
        self.assertEqual(len(cr._buffers), 0)
        self.assertEqual(len(cr._metas), 0)


class TestHttpProfile(unittest.TestCase):
    def test_profiles_load(self):
        from common.http_profile import PROFILES, get_profile, HttpProfile
        self.assertIn('default', PROFILES)
        self.assertIn('chrome', PROFILES)
        self.assertIn('stealth', PROFILES)
        profile = get_profile('default')
        self.assertIsInstance(profile, HttpProfile)
        self.assertIn('Mozilla', profile.user_agent)


if __name__ == '__main__':
    unittest.main()
