import os
import tempfile
import pytest
import socket

from unittest.mock import patch, mock_open
from src.tools import assert_pfo_config_file
from src.tools import mac_only
from src.tools import network_check
from src.tools import deregister


class TestAssertPfoConfigFile:
    
    def test_assert_pfo_config_file_exists(self):
        """Test that function returns True when pfo.json exists in current directory."""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ['pfo.json', 'other_file.txt']
            
            result = assert_pfo_config_file()
            
            assert result is True
            mock_listdir.assert_called_once_with(os.getcwd())
    
    def test_assert_pfo_config_file_not_exists(self):
        """Test that function returns False when pfo.json does not exist in current directory."""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ['other_file.txt', 'another_file.py']
            
            result = assert_pfo_config_file()
            
            assert result is False
            mock_listdir.assert_called_once_with(os.getcwd())
    
    def test_assert_pfo_config_file_empty_directory(self):
        """Test that function returns False when current directory is empty."""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = []
            
            result = assert_pfo_config_file()
            
            assert result is False
            mock_listdir.assert_called_once_with(os.getcwd())
    
    def test_assert_pfo_config_file_case_sensitive(self):
        """Test that function is case sensitive for pfo.json filename."""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ['PFO.JSON', 'Pfo.json', 'pfo.JSON']
            
            result = assert_pfo_config_file()
            
            assert result is False
            mock_listdir.assert_called_once_with(os.getcwd())
    
    def test_assert_pfo_config_file_with_similar_names(self):
        """Test that function only matches exact filename 'pfo.json'."""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ['pfo.json.backup', 'my_pfo.json', 'pfo.jsonl']
            
            result = assert_pfo_config_file()
            
            assert result is False
            mock_listdir.assert_called_once_with(os.getcwd())

class TestNetworkCheck:
    
    def test_network_check_successful_connection(self):
        """Test that function completes successfully when network connection is available."""
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.connect.return_value = None
            
            # Should not raise any exception
            network_check()
            
            mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket_instance.settimeout.assert_called_once_with(5.0)
            mock_socket_instance.connect.assert_called_once_with(("google.com", 80))
    
    def test_network_check_connection_failure(self):
        """Test that function exits when network connection fails."""
        with patch('socket.socket') as mock_socket, \
                patch('src.tools.spinner') as mock_spinner, \
                patch('builtins.exit') as mock_exit:
            
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.connect.side_effect = socket.error("Connection failed")
            
            network_check()
            
            mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket_instance.settimeout.assert_called_once_with(5.0)
            mock_socket_instance.connect.assert_called_once_with(("google.com", 80))
            mock_spinner.fail.assert_called_once_with("Network connection error: Connection failed - The CLI needs a network connection.")
            mock_exit.assert_called_once()
    
    def test_network_check_timeout_error(self):
        """Test that function exits when connection times out."""
        with patch('socket.socket') as mock_socket, \
                patch('src.tools.spinner') as mock_spinner, \
                patch('builtins.exit') as mock_exit:
            
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.connect.side_effect = socket.timeout("Connection timed out")
            
            network_check()
            
            mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket_instance.settimeout.assert_called_once_with(5.0)
            mock_socket_instance.connect.assert_called_once_with(("google.com", 80))
            mock_spinner.fail.assert_called_once_with("Network connection error: Connection timed out - The CLI needs a network connection.")
            mock_exit.assert_called_once()
    
    def test_network_check_socket_creation_and_timeout_setup(self):
        """Test that socket is created with correct parameters and timeout is set."""
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.connect.return_value = None
            
            network_check()
            
            # Verify socket is created with IPv4 and TCP
            mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            # Verify timeout is set to 5 seconds
            mock_socket_instance.settimeout.assert_called_once_with(5.0)

class TestMacOnly:
    
    def test_mac_only_returns_true_on_darwin(self):
        """Test that function returns True when running on macOS (Darwin)."""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Darwin'
            
            result = mac_only()
            
            assert result is True
            mock_system.assert_called_once()
    
    def test_mac_only_returns_false_on_windows(self):
        """Test that function returns False when running on Windows."""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Windows'
            
            result = mac_only()
            
            assert result is False
            mock_system.assert_called_once()
    
    def test_mac_only_returns_false_on_linux(self):
        """Test that function returns False when running on Linux."""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Linux'
            
            result = mac_only()
            
            assert result is False
            mock_system.assert_called_once()
    
    def test_mac_only_returns_false_on_other_systems(self):
        """Test that function returns False when running on other operating systems."""
        test_systems = ['FreeBSD', 'OpenBSD', 'Solaris', 'AIX']
        
        for system in test_systems:
            with patch('platform.system') as mock_system:
                mock_system.return_value = system
                
                result = mac_only()
                
                assert result is False
                mock_system.assert_called_once()
    
    def test_mac_only_case_sensitive(self):
        """Test that function is case sensitive for 'Darwin'."""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'darwin'  # lowercase
            
            result = mac_only()
            
            assert result is False
            mock_system.assert_called_once()


class TestDeregister:
    
    def test_deregister_file_exists_and_removed(self):
        """Test that function removes pfo.json file when it exists."""
        with patch('os.path.abspath') as mock_abspath, \
                patch('os.getcwd') as mock_getcwd, \
                patch('os.path.join') as mock_join, \
                patch('os.path.exists') as mock_exists, \
                patch('os.remove') as mock_remove, \
                patch('src.tools.metadata') as mock_metadata:
            
            mock_getcwd.return_value = '/test/path'
            mock_abspath.return_value = '/test/path'
            mock_join.return_value = '/test/path/pfo.json'
            mock_exists.return_value = True
            mock_metadata.pfo_json_file = 'pfo.json'
            
            deregister()
            
            mock_abspath.assert_called_once_with('/test/path')
            mock_join.assert_called_once_with('/test/path', 'pfo.json')
            mock_exists.assert_called_once_with('/test/path/pfo.json')
            mock_remove.assert_called_once_with('/test/path/pfo.json')
    
    def test_deregister_file_not_exists_shows_info_and_exits(self):
        """Test that function shows info message and exits when pfo.json does not exist."""
        with patch('os.path.abspath') as mock_abspath, \
                patch('os.getcwd') as mock_getcwd, \
                patch('os.path.join') as mock_join, \
                patch('os.path.exists') as mock_exists, \
                patch('os.path.basename') as mock_basename, \
                patch('src.tools.spinner') as mock_spinner, \
                patch('builtins.exit') as mock_exit, \
                patch('src.tools.metadata') as mock_metadata:
            
            mock_getcwd.return_value = '/test/path'
            mock_abspath.return_value = '/test/path'
            mock_join.return_value = '/test/path/pfo.json'
            mock_exists.return_value = False
            mock_basename.return_value = 'path'
            mock_metadata.pfo_json_file = 'pfo.json'
            
            deregister()
            
            mock_abspath.assert_called_once_with('/test/path')
            mock_join.assert_called_once_with('/test/path', 'pfo.json')
            mock_exists.assert_called_once_with('/test/path/pfo.json')
            mock_basename.assert_called_once_with('/test/path')
            mock_spinner.info.assert_called_once_with(
                "This package -- path -- is not currently registered with pfo."
            )
            mock_exit.assert_called_once()
    
    def test_deregister_uses_metadata_pfo_json_file(self):
        """Test that function uses the correct filename from metadata."""
        with patch('os.path.abspath') as mock_abspath, \
                patch('os.getcwd') as mock_getcwd, \
                patch('os.path.join') as mock_join, \
                patch('os.path.exists') as mock_exists, \
                patch('os.remove') as mock_remove, \
                patch('src.tools.metadata') as mock_metadata:
            
            mock_getcwd.return_value = '/test/path'
            mock_abspath.return_value = '/test/path'
            mock_join.return_value = '/test/path/custom.json'
            mock_exists.return_value = True
            mock_metadata.pfo_json_file = 'custom.json'
            
            deregister()
            
            mock_join.assert_called_once_with('/test/path', 'custom.json')
            mock_exists.assert_called_once_with('/test/path/custom.json')
            mock_remove.assert_called_once_with('/test/path/custom.json')
    
    def test_deregister_handles_os_error_during_removal(self):
        """Test that function handles OS errors when trying to remove the file."""
        with patch('os.path.abspath') as mock_abspath, \
                patch('os.getcwd') as mock_getcwd, \
                patch('os.path.join') as mock_join, \
                patch('os.path.exists') as mock_exists, \
                patch('os.remove') as mock_remove, \
                patch('src.tools.metadata') as mock_metadata:
            
            mock_getcwd.return_value = '/test/path'
            mock_abspath.return_value = '/test/path'
            mock_join.return_value = '/test/path/pfo.json'
            mock_exists.return_value = True
            mock_remove.side_effect = OSError("Permission denied")
            mock_metadata.pfo_json_file = 'pfo.json'
            
            
            with pytest.raises(OSError):
                deregister()
            
            mock_exists.assert_called_once_with('/test/path/pfo.json')
            mock_remove.assert_called_once_with('/test/path/pfo.json')
    
    def test_deregister_correct_path_construction(self):
        """Test that function correctly constructs file paths."""
        with patch('os.path.abspath') as mock_abspath, \
                patch('os.getcwd') as mock_getcwd, \
                patch('os.path.join') as mock_join, \
                patch('os.path.exists') as mock_exists, \
                patch('os.remove') as mock_remove, \
                patch('src.tools.metadata') as mock_metadata:
            
            mock_getcwd.return_value = 'current/dir'
            mock_abspath.return_value = '/absolute/current/dir'
            mock_join.return_value = '/absolute/current/dir/pfo.json'
            mock_exists.return_value = True
            mock_metadata.pfo_json_file = 'pfo.json'
            
            deregister()
            
            # Verify the path construction sequence
            mock_getcwd.assert_called_once()
            mock_abspath.assert_called_once_with('current/dir')
            mock_join.assert_called_once_with('/absolute/current/dir', 'pfo.json')


