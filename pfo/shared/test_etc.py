import pytest
from unittest.mock import patch, MagicMock
from pfo.shared import ensure_hosts_entries

class TestEnsureHostsEntries:
    
    @patch('pfo.shared.etc.spinner')
    @patch('pfo.shared.etc.__host_entries_needed_not_in_current_file')
    def test_ensure_hosts_entries_no_entries_needed(self, mock_host_entries, mock_spinner):
        """Test when no host entries are needed."""
        mock_host_entries.return_value = []
        
        ensure_hosts_entries()
        
        mock_spinner.info.assert_called_once_with("No host entries needed.")
        mock_spinner.start.assert_not_called()
        mock_spinner.warn.assert_not_called()
        mock_spinner.succeed.assert_not_called()

    @patch('pfo.shared.etc.spinner')
    @patch('pfo.shared.etc.__host_entries_needed_not_in_current_file')
    def test_ensure_hosts_entries_with_entries_needed(self, mock_host_entries, mock_spinner):
        """Test when host entries are needed."""
        mock_host_entries.return_value = [('127.0.0.1', 'localhost')]
        
        ensure_hosts_entries()
        
        mock_spinner.info.assert_not_called()
        mock_spinner.start.assert_called_once_with("Ensuring host entries...")
        mock_spinner.succeed.assert_called_once_with("Hosts entries ensured successfully.")

    @patch('pfo.shared.etc.spinner')
    @patch('pfo.shared.etc.__host_entries_needed_not_in_current_file')
    def test_ensure_hosts_entries_with_multiple_entries(self, mock_host_entries, mock_spinner):
        """Test when multiple host entries are needed."""
        mock_host_entries.return_value = [
            ('127.0.0.1', 'localhost'),
            ('192.168.1.1', 'gateway')
        ]
        
        ensure_hosts_entries()
        
        mock_spinner.info.assert_not_called()
        mock_spinner.start.assert_called_once_with("Ensuring host entries...")
        mock_spinner.succeed.assert_called_once_with("Hosts entries ensured successfully.")
