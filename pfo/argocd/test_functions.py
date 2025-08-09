import pytest
import requests
import subprocess

from unittest.mock import patch, MagicMock
from pfo.argocd.functions import install_image_updater, wait_for_argocd_server

class TestInstallImageUpdater:
    
    @patch('pfo.argocd.functions.subprocess.run')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_install_image_updater_success(self, mock_spinner, mock_subprocess_run):
        """Test successful installation of ArgoCD Image Updater."""
        # Arrange
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        
        # Act
        install_image_updater()
        
        # Assert
        mock_subprocess_run.assert_called_once_with(
            ["kubectl", "apply", "-n", "argocd", "-f", "https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"],
            check=True,
            capture_output=True,
            text=True
        )
        mock_spinner.fail.assert_not_called()

    @patch('pfo.argocd.functions.subprocess.run')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_install_image_updater_subprocess_error(self, mock_spinner, mock_subprocess_run):
        """Test installation failure due to subprocess error."""
        # Arrange
        error_message = "Command failed"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "kubectl", error_message)
        
        # Act
        result = install_image_updater()
        
        # Assert
        mock_subprocess_run.assert_called_once_with(
            ["kubectl", "apply", "-n", "argocd", "-f", "https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"],
            check=True,
            capture_output=True,
            text=True
        )
        mock_spinner.fail.assert_called_once()
        assert result is None

    @patch('pfo.argocd.functions.subprocess.run')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_install_image_updater_correct_command(self, mock_spinner, mock_subprocess_run):
        """Test that the correct kubectl command is executed."""
        # Arrange
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        
        # Act
        install_image_updater()
        
        # Assert
        expected_command = [
            "kubectl", "apply", "-n", "argocd", "-f", 
            "https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"
        ]
        mock_subprocess_run.assert_called_once_with(
            expected_command,
            check=True,
            capture_output=True,
            text=True
        )

class TestWaitForArgoCdServer:
    
    @patch('pfo.argocd.functions.requests.get')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_wait_for_argocd_server_success_first_attempt(self, mock_spinner, mock_requests_get):
        """Test successful connection on first attempt."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        
        # Act
        wait_for_argocd_server()
        
        # Assert
        mock_spinner.start.assert_called_once_with("Waiting for ArgoCD server to be ready...")
        mock_requests_get.assert_called_once_with(
            "https://argocd.pyflowops.local:30443",
            verify=False,
            allow_redirects=False
        )
        mock_spinner.succeed.assert_called_once_with("ArgoCD server is ready!")
        mock_spinner.fail.assert_not_called()

    @patch('pfo.argocd.functions.time.sleep')
    @patch('pfo.argocd.functions.requests.get')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_wait_for_argocd_server_success_after_retries(self, mock_spinner, mock_requests_get, mock_sleep):
        """Test successful connection after a few retries."""
        # Arrange
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        
        # First two calls fail, third succeeds
        mock_requests_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]
        
        # Act
        wait_for_argocd_server()
        
        # Assert
        mock_spinner.start.assert_called_once_with("Waiting for ArgoCD server to be ready...")
        assert mock_requests_get.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(10)
        mock_spinner.succeed.assert_called_once_with("ArgoCD server is ready!")
        mock_spinner.fail.assert_not_called()

    @patch('pfo.argocd.functions.time.sleep')
    @patch('pfo.argocd.functions.requests.get')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_wait_for_argocd_server_timeout(self, mock_spinner, mock_requests_get, mock_sleep):
        """Test timeout after maximum attempts."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_requests_get.return_value = mock_response
        
        # Act
        wait_for_argocd_server()
        
        # Assert
        mock_spinner.start.assert_called_once_with("Waiting for ArgoCD server to be ready...")
        assert mock_requests_get.call_count == 20
        assert mock_sleep.call_count == 20
        mock_sleep.assert_called_with(10)
        mock_spinner.succeed.assert_not_called()
        mock_spinner.fail.assert_called_once_with("ArgoCD server is not ready after 20 attempts. Please check the logs for more details.")

    @patch('pfo.argocd.functions.time.sleep')
    @patch('pfo.argocd.functions.requests.get')
    @patch('pfo.argocd.functions._argocd_spinner')
    def test_wait_for_argocd_server_various_status_codes(self, mock_spinner, mock_requests_get, mock_sleep):
        """Test handling of various HTTP status codes."""
        # Arrange
        responses = [
            MagicMock(status_code=404),  # Not found
            MagicMock(status_code=500),  # Server error
            MagicMock(status_code=302),  # Redirect
            MagicMock(status_code=200)   # Success
        ]
        mock_requests_get.side_effect = responses
        
        # Act
        wait_for_argocd_server()
        
        # Assert
        mock_spinner.start.assert_called_once_with("Waiting for ArgoCD server to be ready...")
        assert mock_requests_get.call_count == 4
        assert mock_sleep.call_count == 3
        mock_spinner.succeed.assert_called_once_with("ArgoCD server is ready!")
        mock_spinner.fail.assert_not_called()
