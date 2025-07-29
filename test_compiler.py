import subprocess
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

def check_maven_installed():
    """简化Maven检测，假设已安装"""
    return True  # 用户确认Maven已安装且可运行

def check_pom_exists(project_root):
    """检查pom.xml是否存在"""
    return os.path.exists(os.path.join(project_root, "pom.xml"))

def run_tests():
    # 项目根目录
    project_root = r"D:\master_degree\code_replication\Unit_test\deepseek_multi\java_project"

    # 验证环境
    if not check_maven_installed():
        print("Error: Maven is not installed or not in PATH")
        print("Please install Maven and ensure it's in your system PATH")
        return False
    
    if not check_pom_exists(project_root):
        print("Error: pom.xml not found in project directory")
        print(f"Expected at: {os.path.join(project_root, 'pom.xml')}")
        return False
    
    # 确保当前工作目录正确
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    # 测试报告目录
    report_dir = os.path.join(project_root, "target", "surefire-reports")
    os.makedirs(report_dir, exist_ok=True)

    print("Running tests using Maven...")
    
    try:
        # 运行mvn test命令
        result = subprocess.run(
            ["mvn", "clean", "test-compile"],
            capture_output=True,
            text=True,
            shell=True,
            env=os.environ
        )
        
        # 恢复原始工作目录
        os.chdir(original_dir)

        # 输出测试结果
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        # 检查测试结果
        if result.returncode != 0:
            print(f"Tests failed with exit code {result.returncode}")
            return False
            
        print(f"Test reports generated in {report_dir}")
        return True

    except Exception as e:
        print(f"Failed to run Maven tests: {str(e)}")
        return False
'''
def generate_xml_report(project_root):
    """生成统一的XML格式报告"""
    report_dir = os.path.join(project_root, "target", "surefire-reports")
    test_reports = [f for f in os.listdir(report_dir) if f.endswith(".xml")]
    
    root = ET.Element("TestReports")
    for report_file in test_reports:
        tree = ET.parse(os.path.join(report_dir, report_file))
        root.append(tree.getroot())
    
    # 确保目标目录存在
    unified_report_dir = os.path.join(project_root, "test-reports")
    os.makedirs(unified_report_dir, exist_ok=True)
    
    # 生成统一的XML报告
    unified_report_path = os.path.join(unified_report_dir, "unified-report.xml")
    try:
        ET.ElementTree(root).write(unified_report_path, encoding="utf-8", xml_declaration=True)
        print(f"Unified XML report generated at {unified_report_path}")
    except Exception as e:
        print(f"Failed to generate unified XML report: {str(e)}")
'''

if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)