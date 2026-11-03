import unittest
from check_public_privacy import findings

class PublicLinkChecks(unittest.TestCase):
    def setUp(self):
        self.url = 'https://' + 'example.feishu.cn' + '/docx/ApprovedExample'

    def test_private_link_fails_by_default(self):
        self.assertIn('private-workspace-link', findings(self.url))

    def test_exact_link_can_be_authorized(self):
        self.assertNotIn('private-workspace-link', findings('[method](' + self.url + ')', [self.url]))

    def test_other_document_is_not_allowed(self):
        self.assertIn('private-workspace-link', findings(self.url + 'Other', [self.url]))

    def test_query_is_not_implicitly_allowed(self):
        self.assertIn('private-workspace-link', findings(self.url + '?token=example', [self.url]))

    def test_other_rules_remain_active(self):
        self.assertIn('credential', findings(self.url + ' sk-' + 'x' * 30, [self.url]))

    def test_two_links_only_one_authorized(self):
        self.assertIn('private-workspace-link', findings(self.url + '\n' + self.url + 'Private', [self.url]))

if __name__ == '__main__':
    unittest.main()
