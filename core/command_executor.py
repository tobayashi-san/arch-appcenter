"""
Command Executor - Fixed Threading Issues
Fixes GUI calls from background threads that cause segfaults
"""

import subprocess
import threading
import queue
import time
import os
import signal
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QWaitCondition

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

class PasswordManager(QObject):
    """Thread-safe password manager that runs in main thread"""

    password_requested = pyqtSignal(str)  # request_id
    password_provided = pyqtSignal(str, str)  # request_id, password

    def __init__(self):
        super().__init__()
        self.pending_requests = {}
        self.password_cache = None
        self.password_attempts = 0
        self.max_attempts = 3

        # Connect signals
        self.password_requested.connect(self._show_password_dialog)
        self.password_provided.connect(self._handle_password_response)

    def request_password(self, request_id: str) -> Optional[str]:
        """Request password from main thread (thread-safe)"""
        if self.password_cache and self.password_attempts < self.max_attempts:
            return self.password_cache

        # Create wait condition
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
        from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit

        app = QApplication.instance()
        if not app:
            self._complete_request(request_id, None)
            return

        password, ok = QInputDialog.getText(
            None,
            "Sudo Password Required",
            "Please enter your sudo password:",
            echo=QLineEdit.EchoMode.Password
        )

        if ok and password:
            self.password_cache = password
            self.password_attempts = 0
            self._complete_request(request_id, password)
        else:
            self._complete_request(request_id, None)

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
        """Invalidate cached password"""
        self.password_cache = None
        self.password_attempts = 0

    def increment_attempts(self):
        """Increment failed attempts"""
        self.password_attempts += 1
        if self.password_attempts >= self.max_attempts:
            self.password_cache = None

class CommandExecutor(QObject):
    """Thread-safe Command Executor"""

    # Qt Signals
    output_received = pyqtSignal(str, str)  # (output_type, text)
    command_started = pyqtSignal(str)  # command
    command_finished = pyqtSignal(object)  # CommandResult
    password_required = pyqtSignal()  # Passwort benötigt

    def __init__(self, output_callback: Optional[Callable] = None):
        super().__init__()
        self.output_callback = output_callback
        self.current_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.should_cancel = False

        # Thread-safe password manager
        self.password_manager = PasswordManager()

    def is_command_safe(self, command: str) -> bool:
        """Enhanced Command Safety Check"""
        dangerous_patterns = [
            'rm -rf /', 'dd if=', 'mkfs.', 'fdisk', 'parted',
            ':(){ :|:& };:', 'chmod -R 777 /', 'format', 'erase'
        ]

        command_lower = command.lower()
        return not any(pattern in command_lower for pattern in dangerous_patterns)

    def check_pacman_lock(self) -> bool:
        """Check if Pacman is locked"""
        lock_file = "/var/lib/pacman/db.lck"
        return os.path.exists(lock_file)

    def remove_pacman_lock(self) -> bool:
        """Remove Pacman lock after confirmation"""
        try:
            if self.check_pacman_lock():
                # Check if pacman is actually running
                result = subprocess.run(['pgrep', '-x', 'pacman'],
                                      capture_output=True, timeout=5)

                if result.returncode == 0:
                    # Pacman is actually running
                    return False

                # Remove lock file
                subprocess.run(['sudo', 'rm', '-f', '/var/lib/pacman/db.lck'],
                             check=True, timeout=10)
                return True
        except Exception as e:
            print(f"Error removing pacman lock: {e}")
            return False

        return True

    def validate_sudo_password(self, password: str) -> bool:
        """Validate sudo password"""
        try:
            # Test password with harmless sudo command
            process = subprocess.Popen(
                ['sudo', '-S', 'true'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=password + '\n', timeout=5)

            if process.returncode == 0:
                return True
            else:
                self.password_manager.increment_attempts()
                return False

        except Exception:
            return False

    def prepare_command_with_sudo(self, command: str) -> tuple[list, str]:
        """Prepare command with sudo"""
        # Check if sudo is needed
        needs_sudo = command.strip().startswith('sudo')

        if needs_sudo:
            # Remove 'sudo' from beginning and prepare for stdin
            cmd_without_sudo = command.strip()[4:].strip()
            cmd_list = ['sudo', '-S'] + cmd_without_sudo.split()

            # Get password using thread-safe manager
            import uuid
            request_id = str(uuid.uuid4())
            password = self.password_manager.request_password(request_id)

            if not password:
                return None, "Password required but not provided"

            # Validate password
            if not self.validate_sudo_password(password):
                return None, "Invalid password"

            return cmd_list, password + '\n'
        else:
            return command.split(), None

    def execute_command(self, command: str, use_sudo: bool = True, timeout: int = 300) -> CommandResult:
        """Execute a system command safely with fixed threading"""
        start_time = time.time()

        # Basic safety check
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
                # Note: GUI dialogs should be handled in main thread
                # For now, we'll just fail with appropriate message
                return CommandResult(
                    command=command,
                    status=CommandStatus.LOCKED,
                    return_code=-1,
                    stdout="",
                    stderr="Pacman database is locked. Another package manager may be running.",
                    execution_time=time.time() - start_time
                )

        # Prepare command
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

        # Emit started signal
        self.command_started.emit(command)

        try:
            self.is_running = True
            self.should_cancel = False

            # Start process
            self.current_process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )

            # Send password if needed
            if password_input:
                try:
                    self.current_process.stdin.write(password_input)
                    self.current_process.stdin.flush()
                except Exception as e:
                    print(f"Error sending password: {e}")

            # Read output in real-time
            stdout_lines = []
            stderr_lines = []
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()

            def read_stdout():
                try:
                    for line in iter(self.current_process.stdout.readline, ''):
                        if line:
                            stdout_queue.put(line.rstrip())
                        if self.should_cancel:
                            break
                except Exception as e:
                    stdout_queue.put(f"Error reading stdout: {e}")
                finally:
                    stdout_queue.put(None)

            def read_stderr():
                try:
                    for line in iter(self.current_process.stderr.readline, ''):
                        if line:
                            stderr_queue.put(line.rstrip())
                        if self.should_cancel:
                            break
                except Exception as e:
                    stderr_queue.put(f"Error reading stderr: {e}")
                finally:
                    stderr_queue.put(None)

            # Start reader threads
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            # Monitor output
            stdout_finished = False
            stderr_finished = False

            while not (stdout_finished and stderr_finished):
                if self.should_cancel:
                    self.terminate_process()
                    break

                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    self.terminate_process()
                    return CommandResult(
                        command=command,
                        status=CommandStatus.FAILED,
                        return_code=-1,
                        stdout='\n'.join(stdout_lines),
                        stderr='\n'.join(stderr_lines) + '\nTimeout reached',
                        execution_time=time.time() - start_time
                    )

                # Read stdout
                try:
                    line = stdout_queue.get_nowait()
                    if line is None:
                        stdout_finished = True
                    else:
                        stdout_lines.append(line)
                        self.output_received.emit('stdout', line)
                        if self.output_callback:
                            self.output_callback('stdout', line)
                except queue.Empty:
                    pass

                # Read stderr
                try:
                    line = stderr_queue.get_nowait()
                    if line is None:
                        stderr_finished = True
                    else:
                        stderr_lines.append(line)
                        self.output_received.emit('stderr', line)
                        if self.output_callback:
                            self.output_callback('stderr', line)
                except queue.Empty:
                    pass

                time.sleep(0.01)

            # Wait for process to complete
            if self.current_process:
                return_code = self.current_process.wait()
            else:
                return_code = -1

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
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines),
                execution_time=time.time() - start_time
            )

            # Emit finished signal
            self.command_finished.emit(result)
            return result

        except Exception as e:
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

    def check_sudo_available(self) -> bool:
        """Check if sudo is available"""
        try:
            result = subprocess.run(['which', 'sudo'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def reset_sudo_cache(self):
        """Reset cached sudo password"""
        self.password_manager.invalidate_cache()

    def preauth_sudo(self) -> bool:
        """Pre-authenticate sudo to avoid password prompts during execution"""
        try:
            import uuid
            request_id = str(uuid.uuid4())
            password = self.password_manager.request_password(request_id)

            if not password:
                return False

            # Extend sudo timeout
            process = subprocess.Popen(
                ['sudo', '-S', '-v'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=password + '\n', timeout=10)

            if process.returncode == 0:
                print("✅ Sudo pre-authentication successful")
                return True
            else:
                print(f"❌ Sudo pre-authentication failed: {stderr}")
                return False

        except Exception as e:
            print(f"❌ Sudo pre-authentication error: {e}")
            return False


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

        for i, tool in enumerate(self.tools_list):
            progress = int((i / total) * 100)
            self.progress_updated.emit(progress, f"Executing: {tool.name}")

            try:
                result = self.command_executor.execute_command(tool.command)
                self.results.append({
                    'tool': tool,
                    'result': result,
                    'success': result.status.value == "success"
                })

                # Emit output
                if result.stdout:
                    self.output_received.emit('stdout', result.stdout)
                if result.stderr:
                    self.output_received.emit('stderr', result.stderr)

            except Exception as e:
                self.results.append({
                    'tool': tool,
                    'result': None,
                    'success': False,
                    'error': str(e)
                })

        self.progress_updated.emit(100, "Completed")
        self.command_finished.emit(self.results)


# Export classes
__all__ = [
    'CommandExecutor', 'CommandResult', 'CommandStatus',
    'SafeCommandExecutionThread', 'PasswordManager'
]
