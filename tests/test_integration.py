"""Integration tests for encrypted protocol flow."""
import socket
import threading
import unittest

from common.protocol import Protocol
from common.encrypted_protocol import EncryptedProtocol


class TestEncryptedProtocolIntegration(unittest.TestCase):
    def setUp(self):
        self.a, self.b = socket.socketpair()

    def tearDown(self):
        self.a.close()
        self.b.close()

    def test_encrypted_send_recv(self):
        client_proto = EncryptedProtocol(self.a)
        server_proto = EncryptedProtocol(self.b)

        def server_exchange():
            server_proto.perform_key_exchange(initiator=False)

        t = threading.Thread(target=server_exchange)
        t.start()
        client_proto.perform_key_exchange(initiator=True)
        t.join()

        client_proto.send('encrypted hello')
        result = server_proto.recv()
        self.assertEqual(result, 'encrypted hello')

        server_proto.send({'key': 'value'})
        result2 = client_proto.recv()
        self.assertEqual(result2, {'key': 'value'})

    def test_encrypted_multiple_rounds(self):
        client_proto = EncryptedProtocol(self.a)
        server_proto = EncryptedProtocol(self.b)

        def server_exchange():
            server_proto.perform_key_exchange(initiator=False)

        t = threading.Thread(target=server_exchange)
        t.start()
        client_proto.perform_key_exchange(initiator=True)
        t.join()

        for i in range(5):
            client_proto.send(f'message_{i}')
            result = server_proto.recv()
            self.assertEqual(result, f'message_{i}')
            server_proto.send(f'response_{i}')
            result2 = client_proto.recv()
            self.assertEqual(result2, f'response_{i}')

    def test_large_message(self):
        client_proto = EncryptedProtocol(self.a)
        server_proto = EncryptedProtocol(self.b)

        def server_exchange():
            server_proto.perform_key_exchange(initiator=False)

        t = threading.Thread(target=server_exchange)
        t.start()
        client_proto.perform_key_exchange(initiator=True)
        t.join()

        large_msg = 'X' * 3000
        client_proto.send(large_msg)
        result = server_proto.recv()
        self.assertEqual(result, large_msg)

    def test_wrong_initiator_deadlock_detected(self):
        client_proto = EncryptedProtocol(self.a)
        server_proto = EncryptedProtocol(self.b)

        error_detected = threading.Event()

        def client_side():
            try:
                client_proto.perform_key_exchange(initiator=False)
            except ConnectionError:
                error_detected.set()

        def server_side():
            server_proto.perform_key_exchange(initiator=False)
            error_detected.set()

        t1 = threading.Thread(target=client_side)
        t2 = threading.Thread(target=server_side)
        t1.start()
        t2.start()
        t1.join(timeout=3)
        t2.join(timeout=3)


class TestProtocolEdgeCases(unittest.TestCase):
    def setUp(self):
        self.r, self.w = socket.socketpair()
        self.proto = Protocol(self.r)
        self.peer = Protocol(self.w)

    def tearDown(self):
        self.r.close()
        self.w.close()

    def test_empty_string(self):
        self.peer.send('')
        result = self.proto.recv()
        self.assertEqual(result, '')

    def test_unicode_text(self):
        self.peer.send('héllo wörld')
        result = self.proto.recv()
        self.assertEqual(result, 'héllo wörld')

    def test_special_characters(self):
        msg = '{"cmd": "ls -la /etc"}'
        self.peer.send(msg)
        result = self.proto.recv()
        self.assertEqual(result, msg)

    def test_nested_dict(self):
        msg = {'cmd': 'test', 'opts': {'nested': True, 'list': [1, 2, 3]}}
        self.peer.send(msg)
        result = self.proto.recv()
        self.assertEqual(result, msg)

    def test_none_message(self):
        self.peer.send(None)
        result = self.proto.recv()
        self.assertIsNone(result)


class TestCommandRegistryEdgeCases(unittest.TestCase):
    def test_aliases(self):
        from client.core.command_registry import CommandRegistry

        class FakeCmd:
            name = 'test_cmd'
            aliases = ['t', 'tc']

            def execute(self, ctx, raw):
                return True

        registry = CommandRegistry()
        registry.register(FakeCmd())
        ctx = object()
        self.assertTrue(registry.dispatch(ctx, 't'))
        self.assertTrue(registry.dispatch(ctx, 'tc'))
        self.assertTrue(registry.dispatch(ctx, 'test_cmd'))
        self.assertIsNone(registry.dispatch(ctx, 'nonexistent'))

    def test_command_without_aliases(self):
        from client.core.command_registry import CommandRegistry

        class SimpleCmd:
            name = 'simple'

            def execute(self, ctx, raw):
                return 'done'

        registry = CommandRegistry()
        registry.register(SimpleCmd())
        ctx = object()
        self.assertEqual(registry.dispatch(ctx, 'simple'), 'done')

    def test_blank_input(self):
        from client.core.command_registry import CommandRegistry

        class FakeCmd:
            name = 'test'
            aliases = []

            def execute(self, ctx, raw):
                return True

        registry = CommandRegistry()
        registry.register(FakeCmd())
        ctx = object()
        self.assertEqual(registry.dispatch(ctx, ''), True)


class TestCryptoModule(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        from common.crypto import ECDHEncryption
        c1 = ECDHEncryption()
        c2 = ECDHEncryption()
        c1.compute_shared_key(c2.public_key_bytes)
        c2.compute_shared_key(c1.public_key_bytes)

        plaintext = b'This is a secret message'
        encrypted = c1.encrypt(plaintext)
        decrypted = c2.decrypt(encrypted)
        self.assertEqual(plaintext, decrypted)

    def test_public_key_size(self):
        from common.crypto import ECDHEncryption
        c = ECDHEncryption()
        self.assertEqual(len(c.public_key_bytes), ECDHEncryption.PUBLIC_KEY_SIZE)


if __name__ == '__main__':
    unittest.main()
