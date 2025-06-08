import unittest
from email_sender import EmailSender

class TestEmailSender(unittest.TestCase):
    def setUp(self):
        self.sender = EmailSender(dry_run=True)

    def test_email_validation(self):
        valid = "teste@example.com"
        invalid = "email@invalido"
        self.assertTrue(self.sender.validate_email_address(valid))
        self.assertFalse(self.sender.validate_email_address(invalid))

    def test_template_rendering(self):
        context = {"name": "Fulano"}
        result = self.sender.render_template(context)
        self.assertIn("Olá Fulano", result)

    def test_create_email(self):
        html = "<p>Teste</p>"
        msg = self.sender.create_email("teste@example.com", "Fulano", html)
        self.assertEqual(msg['To'], "teste@example.com")
        self.assertIn("Teste", msg.get_body(preferencelist=('html')).get_content())

if __name__ == '__main__':
    unittest.main()
