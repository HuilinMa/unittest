import os
import subprocess
import xml.etree.ElementTree as ET
import glob

# 配置路径
project_root = r"D:\master_degree\code_replication\Unit_test\deepseek_multi\java_project"
test_dir = os.path.join(project_root, "src", "test", "java", "org", "example")
jacoco_report = os.path.join(project_root, "target", "site", "jacoco", "jacoco.xml")

# 1. 统计测试用例总数
def count_test_cases(test_dir):
    count = 0
    for root, _, files in os.walk(test_dir):
        for f in files:
            if f.endswith('.java'):
                count += 1
    return count
 
def run_maven_cmd(cmd):
    result = subprocess.run(cmd, cwd=project_root, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr

# 2. 编译测试用例
# 3. 运行测试用例并生成覆盖率报告
def compile_and_test():
    # 编译
    compile_code, compile_log = run_maven_cmd('mvn test-compile')
    # 测试
    test_code, test_log = run_maven_cmd('mvn test')
    # 生成jacoco报告
    report_code, report_log = run_maven_cmd('mvn jacoco:report')
    return compile_code, compile_log, test_code, test_log, report_code, report_log

# 4. 解析jacoco覆盖率报告
def parse_jacoco_report(jacoco_report):
    if not os.path.exists(jacoco_report):
        return None, None
    tree = ET.parse(jacoco_report)
    root = tree.getroot()
    line_covered = 0
    line_missed = 0
    branch_covered = 0
    branch_missed = 0
    for counter in root.iter('counter'):
        if counter.attrib['type'] == 'LINE':
            line_covered = int(counter.attrib['covered'])
            line_missed = int(counter.attrib['missed'])
        if counter.attrib['type'] == 'BRANCH':
            branch_covered = int(counter.attrib['covered'])
            branch_missed = int(counter.attrib['missed'])
    line_cov = line_covered / (line_covered + line_missed) if (line_covered + line_missed) > 0 else 0
    branch_cov = branch_covered / (branch_covered + branch_missed) if (branch_covered + branch_missed) > 0 else 0
    return line_cov, branch_cov

def parse_surefire_reports():
    surefire_dir = os.path.join(project_root, 'target', 'surefire-reports')
    total = 0
    passed = 0
    for xml_file in glob.glob(os.path.join(surefire_dir, '*.xml')):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            total += int(root.attrib.get('tests', 0))
            passed += int(root.attrib.get('tests', 0)) - int(root.attrib.get('failures', 0)) - int(root.attrib.get('errors', 0)) - int(root.attrib.get('skipped', 0))
        except Exception:
            continue
    return passed, total

def main():
    total_cases = count_test_cases(test_dir)
    print(f"测试用例总数: {total_cases}")
    compile_code, compile_log, test_code, test_log, report_code, report_log = compile_and_test()
    # 编译率/行接受率
    compile_pass = 1 if compile_code == 0 else 0
    print(f"编译通过: {'是' if compile_pass else '否'}")
    print(f"编译率: {compile_pass/1:.2f}")
    # 覆盖率
    line_cov, branch_cov = parse_jacoco_report(jacoco_report)
    if line_cov is not None:
        print(f"代码覆盖率: {line_cov*100:.2f}%")
        print(f"分支覆盖率: {branch_cov*100:.2f}%")
    else:
        print("未找到JaCoCo覆盖率报告，请确认maven已集成jacoco插件并已生成报告。")
    # 新增：统计执行率
    passed, total = parse_surefire_reports()
    exec_rate = passed / total if total > 0 else 0
    print(f"执行通过用例数: {passed}")
    print(f"执行率: {exec_rate:.2f}")

if __name__ == "__main__":
    main()
