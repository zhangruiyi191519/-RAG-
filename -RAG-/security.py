"""
    安全模块，用于对用户输入的文件和提示词进行安全检查
"""
import subprocess
import re
import os
import tempfile
import config_data as config


class FileSecurityScanner:
    def __init__(self):
        self.defender_path = config.exe_path

    # 扫描文件（核心）
    def scan_with_defender(self, file_path: str) -> bool:
        cmd = [
            self.defender_path,
            "-Scan",
            "-ScanType", "3",
            "-File", file_path,
            "-DisableRemediation"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        return result.returncode == 0

    def save_temp_file(self, uploaded_file) -> str:
        suffix = uploaded_file.name.split('.')[-1]

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{suffix}"
        )

        temp_file.write(uploaded_file.read())
        temp_file.close()

        return temp_file.name

    # 保存临时文件，如果文件没有问题则返回文件内容
    def scan_uploaded_file(self, uploaded_file) -> bool:
        file_path = self.save_temp_file(uploaded_file)
        try:
            is_safe = self.scan_with_defender(file_path)

            if not is_safe:
                return False

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        return True

class PromptSecurityChecker(object):
    def __init__(self):
        pass

    # 提示词安全检查
    def check_prompt(self, prompt: str) -> str:
        # 分级别检查提示词
        for pattern in config.HIGH_RISK_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return "HIGH"    # 拒绝执行
        for pattern in config.MIDDLE_RISK_PATTERNS:
            if re.search(pattern, prompt):
                return f"MIDDLE"    # 允许查数据，但是会提示用户结果可能不客观
        return "LOW"
    
    # 执行策略
    def enforce(self, prompt: str) -> str:
        level = self.check_prompt(prompt)

        if level == "HIGH":
            return f"检测到你使用了高危提示词，如{config.high_risk_patterns_examples}，系统拒绝执行"
        elif level == "MIDDLE":
            return f"请减少使用一些比较敏感的提示词，如{config.middle_risk_patterns_examples}，这可能导致结果不客观"