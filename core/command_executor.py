"""
Thread-Safe Fixes for Timer and Sudo Issues
Fixes QTimer thread warnings and sudo execution problems
"""

import subprocess
import threading
import queue
import time
import os
import signal
import re
import shlex
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QWaitCondition, QTimer
from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox

class CommandStatus(Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_PASSWORD = "needs_password"
    LOCKED = "locked"

@dataclass
class CommandResult:
    """Result of command execution"""
    command: str
    status: CommandStatus
    return_code: int
    stdout: str
    stderr: str
    execution_time: float

class CommandSecurity:
    """Enhanced Command Security - Blocks unsafe and problematic commands"""
    
    def __init__(self):
        # Absolut verbotene Befehle (Sicherheitsrisiko)
        self.forbidden_commands = {
            'rm -rf /', 'rm -rf /*', 'rm -rf ~/*',
            'dd if=', 'mkfs.', 'fdisk', 'parted',
            'format', 'erase', 'shutdown', 'reboot',
            ':(){ :|:& };:', 'chmod -R 777 /', 'chown -R',
            'systemctl disable', 'systemctl mask'
        }
        
        # Problematische Befehle (funktionieren nicht richtig in diesem Kontext)
        self.problematic_commands = {
            'cp ': 'cp commands often fail in this context - use package managers instead',
            'mv ': 'mv commands can be unreliable - use install scripts instead', 
            'ln -s': 'symbolic links may not work properly - use absolute paths',
            'curl -o': 'direct file downloads can be problematic - use package managers',
            'wget -O': 'direct file downloads can be problematic - use package managers',
            'tar -x': 'tar extraction should be done in controlled environment',
            'make install': 'use AUR helpers like yay or paru instead'
        }

    def is_command_safe(self, command: str) -> Tuple[bool, Optional[str]]:
        """Comprehensive command safety check"""
        command = command.strip()
        command_lower = command.lower()
        
        # 1. Check forbidden commands
        for forbidden in self.forbidden_commands:
            if forbidden in command_lower:
                return False, f"Forbidden command: {forbidden}"
        
        # 2. Check problematic commands
        for problematic, reason in self.problematic_commands.items():
            if command_lower.startswith(problematic) or f" {problematic}" in command_lower:
                return False, f"Problematic command: {reason}"
        
        # 3. Check dangerous patterns
        dangerous_patterns = [
            r'\*\s*/\s*',    # */ patterns
            r'rm\s+.*\*',    # rm with wildcards
            r'chmod\s+.*\*', # chmod with wildcards
            r'>\s*/dev/',    # redirect to /dev/
            r'\|\s*rm',      # pipe to rm
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return False, f"Dangerous pattern: {pattern}"
        
        # 4. Check path traversal
        if '../' in command or '/..' in command:
            return False, "Path traversal detected"
        
        # 5. Check shell injection (with exceptions for safe commands)
        injection_chars = [';', '&', '`', '$', '(', ')']
        if any(char in command for char in injection_chars):
            # Allow for safe package managers
            safe_exceptions = ['pacman', 'yay', 'paru', 'flatpak', 'systemctl', 'journalctl']
            if not any(safe_cmd in command_lower for safe_cmd in safe_exceptions):
                return False, "Potential shell injection"
        
        return True, None

class ThreadSafePasswordManager(QObject):
    """Thread-safe password manager WITHOUT QTimer issues"""

    password_requested = pyqtSignal(str)  # request_id
    password_provided = pyqtSignal(str, str)  # request_id, password

    def __init__(self):
        super().__init__()
        
        # Password caching - NO QTimer usage!
        self.password_cache = None
        self.password_valid_until = 0
        self.cache_duration = 900  # 15 minutes
        
        # Error handling
        self.password_attempts = 0
        self.max_attempts = 3
        self.last_failure_time = 0
        
        # Thread synchronization
        self.pending_requests = {}
        self._lock = threading.Lock()
        
        # Connect signals
        self.password_requested.connect(self._show_password_dialog)
        self.password_provided.connect(self._handle_password_response)

    def is_password_cached_and_valid(self) -> bool:
        """Check if cached password is still valid - NO QTimer"""
        with self._lock:
            if not self.password_cache:
                return False
            
            # Check time limit
            current_time = time.time()
            if current_time > self.password_valid_until:
                self.password_cache = None
                return False
            
            # Quick sudo session check
            return self.verify_sudo_session_simple()

    def verify_sudo_session_simple(self) -> bool:
        """Simple sudo session check without timer complications"""
        try:
            # Test with harmless sudo command without password
            result = subprocess.run(
                ['sudo', '-n', 'true'],  # -n = non-interactive
                capture_output=True,
                timeout=2
            )
            
            return result.returncode == 0
            
        except Exception:
            return False

    def request_password(self, request_id: str) -> Optional[str]:
        """Request password with intelligent caching - NO QTimer"""
        
        # 1. Check cached password
        if self.is_password_cached_and_valid():
            print("🔐 Using cached password")
            return self.password_cache
        
        # 2. Check rate limiting after failures
        current_time = time.time()
        if (self.password_attempts >= self.max_attempts and 
            current_time - self.last_failure_time < 30):
            print("❌ Too many failed attempts, please wait")
            return None
        
        # 3. New password input required
        print("🔑 Requesting new password input")
        
        # Thread-safe password input
        mutex = QMutex()
        wait_condition = QWaitCondition()

        self.pending_requests[request_id] = {
            'mutex': mutex,
            'condition': wait_condition,
            'password': None,
            'completed': False
        }

        # Request password from main thread
        self.password_requested.emit(request_id)

        # Wait for response (with timeout)
        mutex.lock()
        try:
            if not self.pending_requests[request_id]['completed']:
                wait_condition.wait(mutex, 30000)  # 30 second timeout

            result = self.pending_requests[request_id]['password']
            del self.pending_requests[request_id]
            return result
        finally:
            mutex.unlock()

    def _show_password_dialog(self, request_id: str):
        """Show password dialog in main thread"""
        app = QApplication.instance()
        if not app:
            self._complete_request(request_id, None)
            return

        # Enhanced dialog design
        dialog_title = "Sudo Password Required"
        dialog_text = "Please enter your sudo password to continue:"
        
        # Show attempt count if not first try
        if self.password_attempts > 0:
            dialog_text += f"\n\nAttempt {self.password_attempts + 1} of {self.max_attempts}"

        password, ok = QInputDialog.getText(
            None,
            dialog_title,
            dialog_text,
            echo=QLineEdit.EchoMode.Password
        )

        if ok and password:
            # Test password immediately
            if self.validate_sudo_password(password):
                # Password is correct - cache it with timestamp
                with self._lock:
                    self.password_cache = password
                    self.password_valid_until = time.time() + self.cache_duration
                    self.password_attempts = 0  # Reset counter
                
                print("✅ Password validation successful")
                self._complete_request(request_id, password)
            else:
                # Wrong password
                self.password_attempts += 1
                self.last_failure_time = time.time()
                
                if self.password_attempts >= self.max_attempts:
                    self.show_too_many_attempts_dialog()
                    self._complete_request(request_id, None)
                else:
                    # Show error and try again
                    self.show_wrong_password_dialog(self.password_attempts, request_id)
                
        else:
            # User cancelled
            print("❌ Password input cancelled by user")
            self._complete_request(request_id, None)

    def validate_sudo_password(self, password: str) -> bool:
        """Validate sudo password WITHOUT showing stderr"""
        try:
            # Test with harmless command
            process = subprocess.Popen(
                ['sudo', '-S', 'true'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr but don't show it
                text=True
            )

            # Send password
            stdout, stderr = process.communicate(input=password + '\n', timeout=5)

            # Only check return code, DON'T propagate stderr
            success = (process.returncode == 0)
            
            if success:
                print("🔐 Password validation successful")
            else:
                print("❌ Password validation failed")
                
            return success

        except subprocess.TimeoutExpired:
            print("❌ Password validation timed out")
            return False
        except Exception as e:
            print(f"❌ Password validation error: {e}")
            return False

    def show_wrong_password_dialog(self, attempt: int, request_id: str):
        """Show dialog for wrong password"""
        remaining = self.max_attempts - attempt
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Invalid Password")
        msg.setText("The entered password is incorrect.")
        msg.setInformativeText(f"You have {remaining} attempt(s) remaining.")
        msg.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Retry)
        
        if msg.exec() == QMessageBox.StandardButton.Retry:
            # Show dialog again
            self.password_requested.emit(request_id)
        else:
            self._complete_request(request_id, None)

    def show_too_many_attempts_dialog(self):
        """Show dialog for too many attempts"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Too Many Attempts")
        msg.setText("Too many failed password attempts.")
        msg.setInformativeText("Please wait 30 seconds before trying again.")
        msg.exec()

    def _handle_password_response(self, request_id: str, password: str):
        """Handle password response"""
        self._complete_request(request_id, password)

    def _complete_request(self, request_id: str, password: Optional[str]):
        """Complete password request"""
        if request_id in self.pending_requests:
            request_data = self.pending_requests[request_id]
            request_data['password'] = password
            request_data['completed'] = True
            request_data['condition'].wakeAll()

    def invalidate_cache(self):
        """Invalidate password cache manually"""
        with self._lock:
            self.password_cache = None
            self.password_valid_until = 0
            self.password_attempts = 0
        print("🔐 Password cache invalidated")

    def increment_attempts(self):
        """Increment failed attempts"""
        self.password_attempts += 1
        if self.password_attempts >= self.max_attempts:
            self.password_cache = None

class FixedCommandExecutor(QObject):
    """Fixed Command Executor with proper thread handling and sudo support"""

    # Qt Signals
    output_received = pyqtSignal(str, str)  # (output_type, text)
    command_started = pyqtSignal(str)  # command
    command_finished = pyqtSignal(object)  # CommandResult
    password_required = pyqtSignal()  # Password needed

    def __init__(self, output_callback: Optional[Callable] = None):
        super().__init__()
        self.output_callback = output_callback
        self.current_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.should_cancel = False

        # Enhanced components
        self.password_manager = ThreadSafePasswordManager()
        self.command_security = CommandSecurity()

    def is_command_safe(self, command: str) -> bool:
        """Enhanced Command Safety Check with detailed logging"""
        is_safe, reason = self.command_security.is_command_safe(command)
        
        if not is_safe:
            print(f"❌ Command blocked: {reason}")
        else:
            print(f"✅ Command safety check passed: {command[:50]}...")
            
        return is_safe

    def filter_sudo_prompts(self, stderr: str) -> str:
        """Filter sudo password prompts from stderr"""
        if not stderr:
            return stderr
        
        # Common sudo prompts to filter out
        sudo_prompts = [
            '[sudo] password for',
            'Password:',
            'Enter password:',
            'Sorry, try again.',
            'sudo: 3 incorrect password',
            'sudo: a terminal is required',
            'sudo: a password is required'
        ]
        
        lines = stderr.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Check if line is a sudo prompt
            is_sudo_prompt = any(prompt in line for prompt in sudo_prompts)
            
            if not is_sudo_prompt and line.strip():
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def prepare_command_with_sudo(self, command: str) -> tuple:
        """Prepare command with sudo - FIXED for proper stdin handling"""
        # Check if sudo is needed
        needs_sudo = command.strip().startswith('sudo')

        if needs_sudo:
            # Remove 'sudo' from beginning
            cmd_without_sudo = command.strip()[4:].strip()
            
            # Check if password is already cached and valid
            if self.password_manager.is_password_cached_and_valid():
                print("🔐 Using cached password - preparing -S command")
                # Use -S even with cached password for consistency
                cmd_list = ['sudo', '-S'] + cmd_without_sudo.split()
                
                # Get cached password
                with self.password_manager._lock:
                    password = self.password_manager.password_cache
                
                return cmd_list, password + '\n'
            else:
                # Need new password
                cmd_list = ['sudo', '-S'] + cmd_without_sudo.split()
                
                # Get password using thread-safe manager
                import uuid
                request_id = str(uuid.uuid4())
                password = self.password_manager.request_password(request_id)

                if not password:
                    return None, "Password required but not provided"

                return cmd_list, password + '\n'
        else:
            return command.split(), None

    def execute_command(self, command: str, use_sudo: bool = True, timeout: int = 300) -> CommandResult:
        """Execute command with enhanced security and FIXED sudo handling"""
        start_time = time.time()

        # Enhanced safety check
        if not self.is_command_safe(command):
            return CommandResult(
                command=command,
                status=CommandStatus.FAILED,
                return_code=-1,
                stdout="",
                stderr="Command blocked for safety reasons",
                execution_time=0
            )

        # Check Pacman lock for pacman commands
        if 'pacman' in command.lower():
            if self.check_pacman_lock():
                return CommandResult(
                    command=command,
                    status=CommandStatus.LOCKED,
                    return_code=-1,
                    stdout="",
                    stderr="Pacman database is locked. Another package manager may be running.",
                    execution_time=time.time() - start_time
                )

        # Prepare command with improved sudo handling
        cmd_result = self.prepare_command_with_sudo(command)
        if cmd_result[0] is None:
            return CommandResult(
                command=command,
                status=CommandStatus.NEEDS_PASSWORD,
                return_code=-1,
                stdout="",
                stderr=cmd_result[1],
                execution_time=time.time() - start_time
            )

        cmd_list, password_input = cmd_result

        print(f"🔧 Executing: {' '.join(cmd_list[:3])}... with password: {'Yes' if password_input else 'No'}")

        # Emit started signal
        self.command_started.emit(command)

        try:
            self.is_running = True
            self.should_cancel = False

            # Start process with proper environment
            env = os.environ.copy()
            env['SUDO_ASKPASS'] = '/bin/false'  # Prevent GUI password prompts
            
            self.current_process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )

            # Send password IMMEDIATELY if needed
            if password_input:
                try:
                    print("🔑 Sending password to sudo...")
                    self.current_process.stdin.write(password_input)
                    self.current_process.stdin.flush()
                    # Keep stdin open for potential additional input
                    print("✅ Password sent successfully")
                except Exception as e:
                    print(f"❌ Error sending password: {e}")
                    return CommandResult(
                        command=command,
                        status=CommandStatus.FAILED,
                        return_code=-1,
                        stdout="",
                        stderr=f"Failed to send password: {e}",
                        execution_time=time.time() - start_time
                    )

            # Read output with timeout handling
            try:
                stdout, stderr = self.current_process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                print("⏰ Command timed out, terminating...")
                self.terminate_process()
                stdout, stderr = self.current_process.communicate()
                
                return CommandResult(
                    command=command,
                    status=CommandStatus.FAILED,
                    return_code=-1,
                    stdout=stdout or "",
                    stderr=(stderr or "") + "\nCommand timed out",
                    execution_time=time.time() - start_time
                )

            return_code = self.current_process.returncode

            # Filter stderr to remove sudo prompts
            filtered_stderr = self.filter_sudo_prompts(stderr or "")

            # Emit real-time output (filtered)
            if stdout:
                self.output_received.emit('stdout', stdout)
                if self.output_callback:
                    self.output_callback('stdout', stdout)

            if filtered_stderr:
                self.output_received.emit('stderr', filtered_stderr)
                if self.output_callback:
                    self.output_callback('stderr', filtered_stderr)

            # Determine status
            if self.should_cancel:
                status = CommandStatus.CANCELLED
            elif return_code == 0:
                status = CommandStatus.SUCCESS
            else:
                status = CommandStatus.FAILED

            # Create result
            result = CommandResult(
                command=command,
                status=status,
                return_code=return_code,
                stdout=stdout or "",
                stderr=filtered_stderr,
                execution_time=time.time() - start_time
            )

            print(f"✅ Command completed: {command[:30]}... -> {status.value} (code: {return_code})")

            # Emit finished signal
            self.command_finished.emit(result)
            return result

        except Exception as e:
            print(f"❌ Command execution exception: {e}")
            error_result = CommandResult(
                command=command,
                status=CommandStatus.FAILED,
                return_code=-1,
                stdout="",
                stderr=f"Execution error: {e}",
                execution_time=time.time() - start_time
            )
            self.command_finished.emit(error_result)
            return error_result

        finally:
            self.is_running = False
            self.current_process = None

    def check_pacman_lock(self) -> bool:
        """Check if Pacman is locked"""
        lock_file = "/var/lib/pacman/db.lck"
        return os.path.exists(lock_file)

    def terminate_process(self):
        """Proper process termination"""
        if self.current_process:
            try:
                if os.name != 'nt':
                    # Linux/Unix: Terminate process group
                    os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                    time.sleep(1)
                    if self.current_process.poll() is None:
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                else:
                    # Windows
                    self.current_process.terminate()
                    time.sleep(1)
                    if self.current_process.poll() is None:
                        self.current_process.kill()
            except Exception as e:
                print(f"Error terminating process: {e}")

    def cancel_current_command(self):
        """Cancel the currently running command"""
        if self.is_running:
            self.should_cancel = True
            self.terminate_process()

    def reset_sudo_cache(self):
        """Reset cached sudo password"""
        self.password_manager.invalidate_cache()

    def get_password_cache_status(self) -> dict:
        """Get password cache status for debugging"""
        return {
            'cached': bool(self.password_manager.password_cache),
            'valid': self.password_manager.is_password_cached_and_valid(),
            'attempts': self.password_manager.password_attempts,
            'expires_in': max(0, self.password_manager.password_valid_until - time.time()) if self.password_manager.password_cache else 0
        }


class SafeCommandExecutionThread(QThread):
    """Safe command execution thread that doesn't call GUI functions"""

    progress_updated = pyqtSignal(int, str)  # progress, status
    command_finished = pyqtSignal(object)   # result list
    output_received = pyqtSignal(str, str)   # type, text

    def __init__(self, tools_list, command_executor):
        super().__init__()
        self.tools_list = tools_list
        self.command_executor = command_executor
        self.results = []

    def run(self):
        """Execute tools in background thread safely"""
        total = len(self.tools_list)
        print(f"🚀 Starting batch execution of {total} tools")

        for i, tool in enumerate(self.tools_list):
            progress = int((i / total) * 100)
            self.progress_updated.emit(progress, f"Executing: {tool.name}")

            try:
                print(f"🔧 [{i+1}/{total}] Executing: {tool.name}")
                result = self.command_executor.execute_command(tool.command)
                
                success = result.status.value == "success"
                print(f"{'✅' if success else '❌'} [{i+1}/{total}] {tool.name} -> {result.status.value}")
                
                self.results.append({
                    'tool': tool,
                    'result': result,
                    'success': success
                })

                # Emit output (filtered for sudo prompts)
                if result.stdout:
                    self.output_received.emit('stdout', result.stdout)
                if result.stderr and result.stderr.strip():
                    # Additional filtering for stderr
                    filtered_stderr = self.command_executor.filter_sudo_prompts(result.stderr)
                    if filtered_stderr.strip():
                        self.output_received.emit('stderr', filtered_stderr)

            except Exception as e:
                error_msg = f"Failed to execute {tool.name}: {str(e)}"
                print(f"❌ {error_msg}")
                
                self.results.append({
                    'tool': tool,
                    'result': None,
                    'success': False,
                    'error': str(e)
                })
                
                # Emit error as stderr
                self.output_received.emit('stderr', error_msg)

        self.progress_updated.emit(100, "Completed")
        self.command_finished.emit(self.results)
        
        # Summary
        success_count = sum(1 for r in self.results if r['success'])
        print(f"🎯 Batch execution completed: {success_count}/{total} successful")


# Compatibility aliases for existing code
CommandExecutor = FixedCommandExecutor
PasswordManager = ThreadSafePasswordManager

# Export classes
__all__ = [
    'FixedCommandExecutor', 'CommandExecutor', 'CommandResult', 'CommandStatus',
    'SafeCommandExecutionThread', 'ThreadSafePasswordManager', 'PasswordManager', 'CommandSecurity'
]
