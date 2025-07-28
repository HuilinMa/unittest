import os
import subprocess
import sys
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()
# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("70b_API_KEY"),
    base_url=os.getenv("remote_url")
)

def extract_java_code(response_text):
    """Extract Java code block from response text"""
    start_marker = "```java"
    end_marker = "```"
    start = response_text.find(start_marker) + len(start_marker)
    end = response_text.find(end_marker, start)
    if start != -1 and end != -1:
        return response_text[start:end].strip()
    return ""

def generate_unit_tests(class_name, class_code, error_info=None, attempt=1):
    """Generate unit tests with OpenAI implementation"""
    try:
        # Role setting and prompt construction
        role_setting = """You are an expert Java developer and unit test generator with deep knowledge of JUnit.
Your task is to write comprehensive unit tests that cover all edge cases and follow best practices.<think>\n</think>"""
        
        if error_info:
            prompt = f"""
{role_setting}

Attempt #{attempt} to generate unit tests for class: {class_name}

Previous compilation/test errors:
{error_info}

Class code to test:
{class_code}

Please analyze the errors and generate improved unit tests that:
1. Fix any compilation issues in the test code
2. Address any test failures
3. Maintain full test coverage
<think>\n</think>
"""
        else:
            prompt = f"""
{role_setting}

Initial attempt to generate unit tests for class: {class_name}

Important constraints:
1. Use only basic JUnit 4 annotations (@Test, @BeforeEach, @AfterEach)
2. Do NOT use parameterized tests or any advanced features
3. Keep imports simple (org.junit.jupiter.api only)

Class code to test:
{class_code}

Please generate comprehensive unit tests that:
1. Cover all public methods with basic test cases
2. Include edge cases using standard assertions
3. Follow basic JUnit 4 best practices
<think>\n</think>
"""
        print(client)
        response = client.chat.completions.create(
            model=os.getenv("remote_70b"),
            messages=[
                {"role": "system", "content": "你是人工智能助手"},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        
        # Process streaming response
        response_text = ""
        print('chatting...')

        print(response.__dict__)
        cnt = 0
        for chunk in response:

            if chunk.choices[0].delta.content:
                if cnt % 50 == 0:
                    print(response_text) ###打印思考过程
                response_text += chunk.choices[0].delta.content
            cnt += 1
        
        
        print(f'response: {response_text[:10]}...')
        # Extract and format Java code
        if response_text:
            java_code = extract_java_code(response_text)
            if java_code:
                return f"""// Generated unit tests for {class_name}
// Attempt: {attempt}
// Timestamp: {datetime.now().isoformat()}

{java_code}"""
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    return None

def check_maven_installed():
    """简化Maven检测，假设已安装"""
    return True  # 用户确认Maven已安装且可运行

def check_pom_exists(project_root):
    """检查pom.xml是否存在"""
    return os.path.exists(os.path.join(project_root, "pom.xml"))

def run_maven_compile(project_root):
    """Run Maven test compilation"""
    original_dir = os.getcwd()
    os.chdir(project_root)
    try:
        result = subprocess.run(
            ["mvn","clean", "test-compile"],
            capture_output=True,
            text=True,
            env=os.environ,
            shell=True
        )
        return result
    finally:
        os.chdir(original_dir)

def extract_compilation_errors(output):
    """提取编译错误"""
    errors = []
    for line in output.split('\n'):
        if '[ERROR]' in line:
            # 过滤掉非具体错误的行
            if "COMPILATION ERROR" not in line and "BUILD FAILURE" not in line:
                errors.append(line.strip())
    return "\n".join(errors)

def main():
    """Main function to generate and test unit tests"""
    print('begin')
    max_attempts = 3
    project_root = r"D:\master_degree\code_replication\Unit_test\deepseek_multi\java_project"
    main_dir = os.path.join(project_root, "src", "main", "java", "org", "example")
    test_dir = os.path.join(project_root, "src", "test", "java", "org", "example")
    
    # Create directories if they don't exist
    os.makedirs(main_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    # Check Maven environment
    print('checking maven env')
    if not check_maven_installed():
        print("Error: Maven is not installed or not in PATH")
        sys.exit(1)
    
    if not check_pom_exists(project_root):
        print("Error: pom.xml not found in project directory")
        sys.exit(1)

    # Get all Java source files
    main_files = [f for f in sorted(os.listdir(main_dir))
                 if f.endswith('.java') and not f.endswith('Test.java')]
    
    for main_file in main_files:
        print(f'processing file {main_file}')
        class_name = os.path.splitext(main_file)[0]
        test_file = f"{class_name}Test.java"
        test_file_path = os.path.join(test_dir, test_file)
        
        # Read source code
        with open(os.path.join(main_dir, main_file), "r", encoding="utf-8") as f:
            class_code = f.read()
        print('finishing reading source code')
        # 初始化错误信息
        error_info = None

        # Generate and test with up to max_attempts
        for attempt in range(1, max_attempts + 1):
            # Generate tests
            print('generating tests')
            tests = generate_unit_tests(class_name, class_code, error_info, attempt=attempt)
            if not tests:
                print(f"Failed to generate tests for {class_name} on attempt {attempt}")
                continue
            
            # Write test file
            print('writing')
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(tests)
            
            print(f"Generated tests for {class_name} (attempt {attempt})")
            
            # 运行编译检查
            print(f"Compiling tests for {class_name}...")
            result = run_maven_compile(project_root)
            
            if result.returncode == 0:
                print(f"✅ Tests compiled successfully for {class_name}!")
                break  # 编译成功，跳出循环
                
            # 收集错误信息
            error_info = extract_compilation_errors(result.stderr + result.stdout)
            
            if not error_info:
                error_info = "Compilation failed with unknown errors"
            
            print(f"❌ Compilation failed (attempt {attempt}):")
            print(error_info)
            
        else:  # 所有尝试都失败
            print(f"⚠️ Failed to compile tests after {max_attempts} attempts: {class_name}")

if __name__ == "__main__":
    print('entrance')
    main()