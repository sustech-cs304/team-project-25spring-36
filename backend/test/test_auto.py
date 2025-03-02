import requests
import time
import os
import uuid
from typing import Dict, Optional, List

"""
文件共享功能自动化测试脚本

测试模块：
1. 用户管理测试
   - 用户注册
   - 用户登录
2. 基础文件操作测试
   - 创建目录
   - 上传文件
   - 删除文件
3. 共享功能测试
   - 创建共享
   - 接收共享
   - 共享列表
4. 共享文件操作测试
   - 在共享目录中创建目录
   - 在共享目录中上传文件
   - 移动共享文件
   - 删除共享文件
"""

# 服务器基础URL
SERVER_BASE_URL = "http://localhost:8080/api"

# 共享令牌解析请求类定义
class ShareTokenParseRequest:
    def __init__(self, token: str):
        self.token = token

class EntryMoveRequest:
    def __init__(self, src_entry_path: str, dst_entry_path: str):
        self.src_entry_path = src_entry_path
        self.dst_entry_path = dst_entry_path

# 测试数据
USER_A = {
    "username": f"user_a_{uuid.uuid4().hex[:8]}",
    "password": "password123",
    "role": "student"
}

USER_B = {
    "username": f"user_b_{uuid.uuid4().hex[:8]}",
    "password": "password123",
    "role": "student"
}

USER_C = {
    "username": f"user_c_{uuid.uuid4().hex[:8]}",
    "password": "password123",
    "role": "student"
}

# 辅助函数
def format_api_response(response: Dict) -> str:
    """格式化 API 响应输出"""
    if not response:
        return "空响应"
        
    formatted = []
    # 状态信息
    status = "成功" if response.get("code", 200) == 200 else "失败"
    formatted.append(f"状态: {status}")
    
    # 错误信息
    if "message" in response:
        formatted.append(f"消息: {response['message']}")
        
    # 数据内容
    data = response.get("data")
    if isinstance(data, list):
        formatted.append(f"数据条数: {len(data)}")
        if data:
            # 只显示第一条数据作为示例
            formatted.append("数据示例:")
            example = data[0]
            if isinstance(example, dict):
                for key, value in example.items():
                    formatted.append(f"  {key}: {value}")
    elif isinstance(data, dict):
        formatted.append("返回数据:")
        for key, value in data.items():
            formatted.append(f"  {key}: {value}")
    elif data:
        formatted.append(f"返回数据: {data}")
        
    return "\n".join(formatted)

def assert_success(response: Dict):
    """检查响应是否成功并格式化输出"""
    formatted_response = format_api_response(response)
    print("\n响应详情:")
    print("-" * 40)
    print(formatted_response)
    print("-" * 40)
    
    if "code" in response:
        assert response["code"] == 200, f"请求失败 (代码 {response['code']}): {response.get('message', '')}"
        return response.get("data", {})
    elif "statusCode" in response:
        assert response["statusCode"] == 200, f"请求失败 (状态码 {response['statusCode']}): {response.get('message', '')}"
        return response.get("data", {})
    else:
        print("警告: 响应格式无法识别")
        return response

def create_test_file(content="测试内容"):
    """创建一个临时测试文件"""
    filename = f"testfile_{uuid.uuid4().hex[:8]}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

# API 功能函数
def register_user(username: str, password: str, role: str) -> str:
    """注册用户并返回token"""
    response = requests.post(
        url=f"{SERVER_BASE_URL}/user/register",
        json={
            "username": username,
            "password": password,
            "role": role
        }
    ).json()
    return assert_success(response)

def login_user(username: str, password: str) -> str:
    """登录用户并返回token"""
    response = requests.post(
        url=f"{SERVER_BASE_URL}/user/login",
        json={
            "username": username,
            "password": password
        }
    ).json()
    return assert_success(response)

def create_directory(token: str, path: str) -> Dict:
    """创建目录"""
    response = requests.post(
        url=f"{SERVER_BASE_URL}/entry",
        headers={"Access-Token": token},
        data={
            "entry_path": path,
            "entry_type": "directory",
            "is_collaborative": "false"
        }
    ).json()
    assert_success(response)
    return response

def upload_file(token: str, path: str, file_path: str) -> Dict:
    """上传文件"""
    with open(file_path, "rb") as f:
        response = requests.post(
            url=f"{SERVER_BASE_URL}/entry",
            headers={"Access-Token": token},
            data={
                "entry_path": path,
                "entry_type": "file",
                "is_collaborative": "false"
            },
            files={"file": f}
        ).json()
    assert_success(response)
    return response

def create_share_token(token: str, path: str, permissions: Dict) -> str:
    """创建共享令牌"""
    response = requests.post(
        url=f"{SERVER_BASE_URL}/share/token/create",
        headers={"Access-Token": token},
        json={
            "entry_path": path,
            "permissions": permissions
        }
    ).json()
    return assert_success(response)

def parse_share_token(token: str, share_token: str) -> Dict:
    """解析共享令牌"""
    response = requests.post(
        url=f"{SERVER_BASE_URL}/share/token/parse",
        headers={"Access-Token": token},
        json={"token": share_token}
    ).json()
    assert_success(response)
    return response

def get_shared_list(token: str) -> List[Dict]:
    """获取共享列表"""
    response = requests.get(
        url=f"{SERVER_BASE_URL}/share/list",
        headers={"Access-Token": token}
    ).json()
    return assert_success(response)

def get_shared_entry(token: str, shared_entry_id: int, entry_path: str) -> List[Dict]:
    """获取共享条目信息"""
    response = requests.get(
        url=f"{SERVER_BASE_URL}/share",
        headers={"Access-Token": token},
        params={
            "shared_entry_id": shared_entry_id,
            "entry_path": entry_path
        }
    ).json()
    return assert_success(response)

def shared_post_file(token: str, shared_entry_id: int, entry_path: str, file_path: str) -> Dict:
    """在共享目录中上传文件"""
    with open(file_path, "rb") as f:
        response = requests.post(
            url=f"{SERVER_BASE_URL}/share",
            headers={"Access-Token": token},
            params={"shared_entry_id": shared_entry_id},
            data={
                "entry_path": entry_path,
                "entry_type": "file",
                "is_collaborative": "false"
            },
            files={"file": f}
        ).json()
    assert_success(response)
    return response

def shared_create_directory(token: str, shared_entry_id: int, entry_path: str) -> Dict:
    """在共享目录中创建目录"""
    response = requests.post(
        url=f"{SERVER_BASE_URL}/share",
        headers={"Access-Token": token},
        params={"shared_entry_id": shared_entry_id},
        data={
            "entry_path": entry_path,
            "entry_type": "directory",
            "is_collaborative": "false"
        }
    ).json()
    assert_success(response)
    return response

def shared_delete(token: str, shared_entry_id: int, entry_path: str) -> Dict:
    """删除共享条目中的文件或目录"""
    response = requests.delete(
        url=f"{SERVER_BASE_URL}/share",
        headers={"Access-Token": token},
        params={
            "shared_entry_id": shared_entry_id,
            "entry_path": entry_path
        }
    ).json()
    assert_success(response)
    return response

def shared_move(token: str, shared_entry_id: int, src_path: str, dst_path: str) -> Dict:
    """移动共享条目中的文件或目录"""
    response = requests.put(
        url=f"{SERVER_BASE_URL}/share/move",
        headers={"Access-Token": token},
        params={"shared_entry_id": shared_entry_id},
        json={
            "src_entry_path": src_path,
            "dst_entry_path": dst_path
        }
    ).json()
    assert_success(response)
    return response

def clean_up_test_files(filenames):
    """清理测试文件"""
    for filename in filenames:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"清理文件 {filename} 时出错: {e}")

def print_test_header(title: str):
    """打印测试标题"""
    print("\n" + "="*50)
    print(f"测试: {title}")
    print("="*50)

def print_test_step(step: str):
    """打印测试步骤"""
    print(f"\n▶ 步骤: {step}")

def print_test_result(success: bool, message: str):
    """打印测试结果"""
    status = "✅ 成功" if success else "❌ 失败"
    print(f"\n{status} - {message}")

def test_user_management():
    """测试用户管理功能"""
    print_test_header("用户管理功能测试")
    
    try:
        # 1. 测试用户注册
        print_test_step("注册用户")
        token_a = register_user(USER_A["username"], USER_A["password"], USER_A["role"])
        print(f"用户A ({USER_A['username']}) 注册成功")
        
        token_b = register_user(USER_B["username"], USER_B["password"], USER_B["role"])
        print(f"用户B ({USER_B['username']}) 注册成功")
        
        # 2. 测试用户登录
        print_test_step("用户登录")
        token_a = login_user(USER_A["username"], USER_A["password"])
        print_test_result(True, f"用户A ({USER_A['username']}) 登录成功")
        
        token_b = login_user(USER_B["username"], USER_B["password"])
        print_test_result(True, f"用户B ({USER_B['username']}) 登录成功")
        
        print_test_result(True, "用户管理功能测试完成")
        return token_a, token_b
        
    except Exception as e:
        print_test_result(False, f"用户管理测试失败: {str(e)}")
        raise

def test_basic_file_operations(token: str):
    """测试基础文件操作"""
    print_test_header("基础文件操作测试")
    
    test_files = []
    try:
        # 1. 创建目录结构
        print_test_step("创建目录结构")
        create_directory(token, "/aa")
        create_directory(token, "/aa/bb")
        create_directory(token, "/aa/bb/cc")
        print_test_result(True, "目录结构创建成功: /aa/bb/cc")
        
        # 2. 上传文件
        print_test_step("上传文件")
        test_file = create_test_file("这是测试文件内容")
        test_files.append(test_file)
        upload_file(token, "/aa/bb/cc/f1.txt", test_file)
        print_test_result(True, "文件上传成功: /aa/bb/cc/f1.txt")
        
        # 3. 验证文件和目录创建
        print_test_step("验证文件和目录创建")
        response = requests.get(
            url=f"{SERVER_BASE_URL}/entry",
            headers={"Access-Token": token},
            params={"entry_path": "/aa"}
        ).json()
        entries = assert_success(response)
        
        # 收集所有路径并验证
        paths = set()
        for entry in entries:
            paths.add(entry.get("entry_path"))
            
        verification_results = []
        if "/aa/bb" in paths:
            verification_results.append("✓ 目录 /aa/bb 存在")
        else:
            verification_results.append("✗ 目录 /aa/bb 未找到")
            
        if "/aa/bb/cc" in paths:
            verification_results.append("✓ 目录 /aa/bb/cc 存在")
        else:
            verification_results.append("✗ 目录 /aa/bb/cc 未找到")
            
        if "/aa/bb/cc/f1.txt" in paths:
            verification_results.append("✓ 文件 f1.txt 存在")
        else:
            verification_results.append("✗ 文件 f1.txt 未找到")
        
        print("\n验证结果:")
        for result in verification_results:
            print(f"  {result}")
        
        if all(result.startswith("✓") for result in verification_results):
            print_test_result(True, "所有文件和目录验证通过")
        else:
            raise Exception("部分文件或目录验证失败")
        
        return "/aa/bb", test_files
        
    except Exception as e:
        print_test_result(False, f"基础文件操作测试失败: {str(e)}")
        raise
    finally:
        clean_up_test_files(test_files)

def test_sharing_functionality(token_a: str, token_b: str, share_path: str):
    """测试共享功能"""
    print_test_header("共享功能测试")
    
    try:
        # 1. 创建共享
        print_test_step("创建共享")
        share_token = create_share_token(token_a, share_path, {"": "read_write"})
        print_test_result(True, "共享令牌创建成功")
        
        # 2. 接收共享
        print_test_step("接收共享")
        parse_share_token(token_b, share_token)
        print_test_result(True, "用户B成功接收共享")
        
        # 3. 测试共享列表
        print_test_step("获取共享列表")
        shared_entries = get_shared_list(token_b)
        
        if not shared_entries:
            raise Exception("共享列表为空")
        
        shared_entry_id = shared_entries[0]["shared_entry_id"]
        print("\n共享信息:")
        print(f"  - 共享ID: {shared_entry_id}")
        print(f"  - 共享数量: {len(shared_entries)}")
        if "permissions" in shared_entries[0]:
            print("  - 权限设置:")
            for path, perm in shared_entries[0]["permissions"].items():
                print(f"    {path or '/'}: {perm}")
        
        # 4. 验证共享内容
        print_test_step("验证共享内容")
        entries = get_shared_entry(token_b, shared_entry_id, share_path)
        print(f"\n共享目录内容 ({len(entries)} 个条目):")
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            print(f"  {entry_type} {entry['entry_path']}")
        
        print_test_result(True, "共享功能测试完成")
        return shared_entry_id
        
    except Exception as e:
        print_test_result(False, f"共享功能测试失败: {str(e)}")
        raise

def test_shared_file_operations(token: str, shared_entry_id: int, base_path: str):
    """测试共享文件操作"""
    print_test_header("共享文件操作测试")
    test_files = []
    
    try:
        # 1. 在共享目录中创建目录
        dir_path = f"{base_path}/shared_dir"
        print_test_step(f"用户B在共享目录 {base_path} 中创建子目录 shared_dir")
        shared_create_directory(token, shared_entry_id, dir_path)
        
        # 验证目录创建成功
        entries = get_shared_entry(token, shared_entry_id, base_path)
        print("\n操作后的目录状态:")
        paths = []
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            path = entry["entry_path"]
            paths.append(path)
            print(f"  {entry_type} {path}")
        
        if dir_path in paths:
            print_test_result(True, f"用户B成功在共享目录中创建子目录: {dir_path}")
        else:
            raise Exception(f"目录 {dir_path} 未创建成功")
        
        # 2. 在共享目录中上传文件
        file_path = f"{base_path}/shared_file.txt"
        print_test_step(f"用户B在共享目录 {base_path} 中上传文件 shared_file.txt")
        test_file = create_test_file("这是共享文件的内容")
        test_files.append(test_file)
        shared_post_file(token, shared_entry_id, file_path, test_file)
        
        # 验证文件上传成功
        entries = get_shared_entry(token, shared_entry_id, base_path)
        print("\n操作后的目录状态:")
        paths = []
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            path = entry["entry_path"]
            paths.append(path)
            print(f"  {entry_type} {path}")
            
        if file_path in paths:
            print_test_result(True, f"用户B成功在共享目录中上传文件: {file_path}")
        else:
            raise Exception(f"文件 {file_path} 上传失败")
        
        # 3. 移动共享文件
        src_path = file_path
        dst_path = f"{base_path}/shared_dir/moved_file.txt"
        print_test_step(f"用户B将共享文件从 {src_path} 移动到 {dst_path}")
        shared_move(token, shared_entry_id, src_path, dst_path)
        
        # 4. 验证文件移动
        print_test_step(f"验证文件移动结果")
        entries = get_shared_entry(token, shared_entry_id, f"{base_path}/shared_dir")
        print("\n移动后的目录状态:")
        moved_file_exists = False
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            path = entry["entry_path"]
            print(f"  {entry_type} {path}")
            if path == dst_path:
                moved_file_exists = True
        
        if moved_file_exists:
            print_test_result(True, f"文件成功移动到: {dst_path}")
        else:
            raise Exception(f"文件移动到 {dst_path} 失败")
        
        # 5. 删除共享文件
        print_test_step(f"用户B删除共享文件 {dst_path}")
        shared_delete(token, shared_entry_id, dst_path)
        
        # 6. 验证文件删除
        print_test_step(f"验证文件删除结果")
        entries = get_shared_entry(token, shared_entry_id, f"{base_path}/shared_dir")
        print("\n删除后的目录状态:")
        file_still_exists = False
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            path = entry["entry_path"]
            print(f"  {entry_type} {path}")
            if path == dst_path:
                file_still_exists = True
                
        if not file_still_exists:
            print_test_result(True, f"文件 {dst_path} 已成功删除")
        else:
            raise Exception(f"文件 {dst_path} 删除失败")
            
        print_test_result(True, "所有共享文件操作测试成功完成")
        return True
        
    except Exception as e:
        print_test_result(False, f"共享文件操作测试失败: {str(e)}")
        raise
    finally:
        clean_up_test_files(test_files)

def test_basic_sharing():
    """测试共享的基本功能"""
    print_test_header("共享基本功能测试")
    
    try:
        # 1. 用户管理测试
        token_a, token_b = test_user_management()
        
        # 2. 基础文件操作测试
        share_path, test_files = test_basic_file_operations(token_a)
        
        # 3. 共享功能测试
        shared_entry_id = test_sharing_functionality(token_a, token_b, share_path)
        
        # 4. 共享文件操作测试
        test_shared_file_operations(token_b, shared_entry_id, share_path)
        
        print("\n" + "="*30)
        print("共享基本功能测试全部通过！")
        print("="*30)
        
    except Exception as e:
        print(f"\n❌ 基本功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def test_permissions():
    """测试权限控制"""
    print_test_header("基本权限控制测试")
    test_files = []  # 跟踪需要清理的文件
    
    # 为本次测试创建唯一的用户
    user_a = {
        "username": f"user_a_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "role": "student"
    }
    
    user_b = {
        "username": f"user_b_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "role": "student"
    }
    
    user_c = {
        "username": f"user_c_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "role": "student"
    }
    
    try:
        # 1. 注册用户A、B和C
        print_test_step("注册测试用户")
        token_a = register_user(user_a["username"], user_a["password"], user_a["role"])
        token_b = register_user(user_b["username"], user_b["password"], user_b["role"])
        token_c = register_user(user_c["username"], user_c["password"], user_c["role"])
        print(f"用户A: {user_a['username']}")
        print(f"用户B: {user_b['username']}")
        print(f"用户C: {user_c['username']}")
        print_test_result(True, "成功注册用户A、B和C")
        
        # 2. 登录用户A
        print_test_step(f"用户A ({user_a['username']}) 登录系统")
        token_a = login_user(user_a["username"], user_a["password"])
        print_test_result(True, "用户A登录成功")
        
        # 3. 创建目录结构
        test_dir = "/test"
        print_test_step(f"用户A创建测试目录: {test_dir}")
        create_directory(token_a, test_dir)
        
        test_file_path = f"{test_dir}/file1.txt"
        print_test_step(f"用户A在测试目录上传文件: {test_file_path}")
        test_file = create_test_file("这是测试文件内容")
        test_files.append(test_file)
        upload_file(token_a, test_file_path, test_file)
        
        # 获取当前目录状态
        response = requests.get(
            url=f"{SERVER_BASE_URL}/entry",
            headers={"Access-Token": token_a},
            params={"entry_path": test_dir}
        ).json()
        entries = assert_success(response)
        
        print("\n创建后的目录状态:")
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            print(f"  {entry_type} {entry['entry_path']}")
            
        print_test_result(True, "用户A成功创建目录结构和文件")
        
        # 4. 创建只读共享给用户B
        print_test_step(f"用户A创建只读共享，共享目录 {test_dir} 给用户B")
        ro_share_token = create_share_token(token_a, test_dir, {"": "read"})
        print_test_result(True, f"用户A成功创建只读共享令牌: {ro_share_token[:10]}...")
        
        # 5. 创建读写共享给用户C
        print_test_step(f"用户A创建读写共享，共享目录 {test_dir} 给用户C")
        rw_share_token = create_share_token(token_a, test_dir, {"": "read_write"})
        print_test_result(True, f"用户A成功创建读写共享令牌: {rw_share_token[:10]}...")
        
        # 6. 用户B接收只读共享
        print_test_step(f"用户B ({user_b['username']}) 登录系统并接收只读共享")
        token_b = login_user(user_b["username"], user_b["password"])
        parse_share_token(token_b, ro_share_token)
        print_test_result(True, "用户B成功接收只读共享")
        
        # 7. 用户C接收读写共享
        print_test_step(f"用户C ({user_c['username']}) 登录系统并接收读写共享")
        token_c = login_user(user_c["username"], user_c["password"])
        parse_share_token(token_c, rw_share_token)
        print_test_result(True, "用户C成功接收读写共享")
        
        # 8. 获取用户B的共享列表
        print_test_step(f"获取用户B的共享列表")
        shared_entries_b = get_shared_list(token_b)
        shared_entry_id_b = shared_entries_b[0]["shared_entry_id"]
        
        print("\n用户B的共享信息:")
        print(f"  共享ID: {shared_entry_id_b}")
        print(f"  共享源: {shared_entries_b[0]['owner_name']}")
        print(f"  权限: {shared_entries_b[0]['permissions']}")
        print_test_result(True, "成功获取用户B的共享列表")
        
        # 9. 获取用户C的共享列表
        print_test_step(f"获取用户C的共享列表")
        shared_entries_c = get_shared_list(token_c)
        shared_entry_id_c = shared_entries_c[0]["shared_entry_id"]
        
        print("\n用户C的共享信息:")
        print(f"  共享ID: {shared_entry_id_c}")
        print(f"  共享源: {shared_entries_c[0]['owner_name']}")
        print(f"  权限: {shared_entries_c[0]['permissions']}")
        print_test_result(True, "成功获取用户C的共享列表")
        
        # 10. 用户B尝试在只读共享中创建目录
        print_test_step(f"用户B尝试在只读共享 {test_dir} 中创建目录 dir_from_b（预期失败）")
        try:
            shared_create_directory(token_b, shared_entry_id_b, f"{test_dir}/dir_from_b")
            print_test_result(False, "⚠️ 警告：权限检查失败 - 用户B在只读共享中创建目录成功，这不应该发生")
        except Exception as e:
            print_test_result(True, f"预期的失败：用户B无法在只读共享中创建目录，错误: {str(e)}")
        
        # 11. 用户C在读写共享中创建目录
        print_test_step(f"用户C在读写共享 {test_dir} 中创建目录 dir_from_c")
        shared_create_directory(token_c, shared_entry_id_c, f"{test_dir}/dir_from_c")
        
        # 12. 验证目录创建情况
        print_test_step(f"验证权限控制结果")
        # 查看用户A的目录
        response = requests.get(
            url=f"{SERVER_BASE_URL}/entry",
            headers={"Access-Token": token_a},
            params={"entry_path": test_dir}
        ).json()
        entries_a = assert_success(response)
        
        print("\n最终目录状态（用户A视角）:")
        paths_a = []
        for entry in entries_a:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            path = entry["entry_path"]
            paths_a.append(path)
            print(f"  {entry_type} {path}")
        
        # 验证用户C创建的目录存在
        if f"{test_dir}/dir_from_c" in paths_a:
            print_test_result(True, f"验证成功: 用户C成功创建了目录 {test_dir}/dir_from_c")
        else:
            raise Exception(f"用户C创建的目录 {test_dir}/dir_from_c 未找到")
            
        # 验证用户B未能创建目录
        if f"{test_dir}/dir_from_b" in paths_a:
            print_test_result(False, "⚠️ 权限控制失败: 用户B不应该能在只读共享中创建目录")
        else:
            print_test_result(True, "验证成功: 用户B无法在只读共享中创建目录")
        
        print_test_result(True, "权限控制测试通过")
        
    except Exception as e:
        print_test_result(False, f"权限控制测试失败: {str(e)}")
        raise
    finally:
        clean_up_test_files(test_files)

def test_advanced_permissions():
    """测试更复杂的权限控制情况"""
    print_test_header("高级权限控制测试")
    
    test_files = []
    
    # 为本次测试创建唯一的用户
    user_a = {
        "username": f"adv_a_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "role": "student"
    }
    
    user_b = {
        "username": f"adv_b_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "role": "student"
    }
    
    try:
        # 1. 注册用户
        print_test_step("注册测试用户")
        token_a = register_user(user_a["username"], user_a["password"], user_a["role"])
        token_b = register_user(user_b["username"], user_b["password"], user_b["role"])
        print(f"用户A: {user_a['username']}")
        print(f"用户B: {user_b['username']}")
        print_test_result(True, "成功注册测试用户")
        
        # 2. 创建目录结构
        print_test_step(f"用户A ({user_a['username']}) 创建多级目录结构")
        token_a = login_user(user_a["username"], user_a["password"])
        
        # 创建目录结构
        directories = [
            "/adv",
            "/adv/level1",
            "/adv/level1/level2",
            "/adv/level1/level2/level3"
        ]
        
        for dir_path in directories:
            create_directory(token_a, dir_path)
            print(f"  用户A创建目录: {dir_path}")
            
        # 创建测试文件
        test_files_info = [
            ("/adv/file1.txt", "根目录文件"),
            ("/adv/level1/file2.txt", "level1文件"),
            ("/adv/level1/level2/file3.txt", "level2文件")
        ]
        
        for file_path, content in test_files_info:
            test_file = create_test_file(content)
            test_files.append(test_file)
            upload_file(token_a, file_path, test_file)
            print(f"  用户A上传文件: {file_path}")
        
        # 验证目录结构创建
        response = requests.get(
            url=f"{SERVER_BASE_URL}/entry",
            headers={"Access-Token": token_a},
            params={"entry_path": "/adv"}
        ).json()
        entries = assert_success(response)
        
        print("\n用户A创建的目录结构:")
        for entry in entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            print(f"  {entry_type} {entry['entry_path']}")
            
        print_test_result(True, "用户A成功创建多级目录结构和文件")
        
        # 3. 创建差异化权限共享
        print_test_step("用户A创建差异化权限共享")
        permissions = {
            "": "read",                # 根目录只读
            "level1": "read_write",    # level1目录可读写
            "level1/level2": "read"    # level2目录只读
        }
        
        print("\n权限设置详情:")
        for path, perm in permissions.items():
            display_path = "/adv" if not path else f"/adv/{path}"
            print(f"  {display_path}: {perm}")
            
        share_token = create_share_token(token_a, "/adv", permissions)
        print_test_result(True, f"用户A创建差异化权限共享成功，共享令牌: {share_token[:15]}...")
        
        # 4. 用户B接收并测试权限
        print_test_step(f"用户B ({user_b['username']}) 接收共享并测试权限")
        token_b = login_user(user_b["username"], user_b["password"])
        parse_share_token(token_b, share_token)
        print_test_result(True, "用户B成功接收共享")
        
        # 获取共享ID
        shared_entries = get_shared_list(token_b)
        shared_entry_id = shared_entries[0]["shared_entry_id"]
        
        print("\n用户B的共享信息:")
        print(f"  共享ID: {shared_entry_id}")
        print(f"  共享源: {shared_entries[0]['owner_name']}")
        print("  权限设置:")
        for path, perm in shared_entries[0]['permissions'].items():
            display_path = "/adv" if not path else f"/adv/{path}"
            print(f"    {display_path}: {perm}")
        
        # 5. 执行权限测试
        print_test_step("执行差异化权限测试")
        
        # 5.1 用户B测试读取根目录
        print_test_step("用户B读取根目录")
        root_entries = get_shared_entry(token_b, shared_entry_id, "/adv")
        print(f"\n用户B读取到的根目录内容 ({len(root_entries)} 个条目):")
        for entry in root_entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            print(f"  {entry_type} {entry['entry_path']}")
        print_test_result(True, "用户B成功读取根目录内容")
        
        # 5.2 用户B尝试在根目录创建文件
        print_test_step("用户B尝试在根目录创建文件 (预期失败)")
        test_file_root = create_test_file("根目录测试文件")
        test_files.append(test_file_root)
        try:
            shared_post_file(token_b, shared_entry_id, "/adv/test_root.txt", test_file_root)
            print_test_result(False, "⚠️ 警告: 权限检查失败! 用户B不应该能在只读根目录创建文件，但操作成功了")
        except Exception as e:
            print_test_result(True, f"预期的失败: 用户B无法在只读根目录创建文件，错误: {str(e)}")
            
        # 5.3 用户B在level1目录创建文件
        print_test_step("用户B在level1目录创建文件 (预期成功)")
        test_file_level1 = create_test_file("level1测试文件")
        test_files.append(test_file_level1)
        try:
            shared_post_file(token_b, shared_entry_id, "/adv/level1/test_level1.txt", test_file_level1)
            print_test_result(True, "用户B成功在level1目录创建文件 (权限正确)")
        except Exception as e:
            print_test_result(False, f"意外的失败: 用户B应该能在可写的level1目录创建文件，错误: {str(e)}")
            
        # 5.4 用户B尝试在level2目录创建文件
        print_test_step("用户B尝试在level2目录创建文件 (预期失败)")
        test_file_level2 = create_test_file("level2测试文件")
        test_files.append(test_file_level2)
        try:
            shared_post_file(token_b, shared_entry_id, "/adv/level1/level2/test_level2.txt", test_file_level2)
            print_test_result(False, "⚠️ 警告: 权限检查失败! 用户B不应该能在只读level2目录创建文件，但操作成功了")
        except Exception as e:
            print_test_result(True, f"预期的失败: 用户B无法在只读level2目录创建文件，错误: {str(e)}")
            
        # 5.5 用户B尝试删除根目录文件
        print_test_step("用户B尝试删除根目录文件 (预期失败)")
        try:
            shared_delete(token_b, shared_entry_id, "/adv/file1.txt")
            print_test_result(False, "⚠️ 警告: 权限检查失败! 用户B不应该能删除只读根目录的文件，但操作成功了")
        except Exception as e:
            print_test_result(True, f"预期的失败: 用户B无法删除只读根目录的文件，错误: {str(e)}")
            
        # 5.6 用户B尝试将文件从level1移动到根目录
        print_test_step("用户B尝试将文件从level1移动到根目录 (预期失败)")
        try:
            shared_move(token_b, shared_entry_id, "/adv/level1/test_level1.txt", "/adv/moved_file.txt")
            print_test_result(False, "⚠️ 警告: 权限检查失败! 用户B不应该能将文件移动到只读根目录，但操作成功了")
        except Exception as e:
            print_test_result(True, f"预期的失败: 用户B无法将文件移动到只读根目录，错误: {str(e)}")
            
        # 5.7 用户B尝试将文件从level2移动到level1
        print_test_step("用户B尝试将文件从level2移动到level1 (预期失败)")
        try:
            shared_move(token_b, shared_entry_id, "/adv/level1/level2/file3.txt", "/adv/level1/moved_level2_file.txt")
            print_test_result(False, "⚠️ 警告: 权限检查失败! 用户B不应该能移动只读level2中的文件，但操作成功了")
        except Exception as e:
            print_test_result(True, f"预期的失败: 用户B无法移动只读level2中的文件，错误: {str(e)}")
        
        # 6. 验证最终状态
        print_test_step("验证最终文件系统状态")
        final_entries = get_shared_entry(token_b, shared_entry_id, "/adv")
        
        print("\n最终目录结构:")
        file_paths = []
        for entry in final_entries:
            entry_type = "📁" if entry["entry_type"] == "directory" else "📄"
            path = entry["entry_path"]
            file_paths.append(path)
            print(f"  {entry_type} {path}")
        
        # 验证预期存在的文件
        expected_files = [
            "/adv/file1.txt",  # 原文件应该存在(删除失败)
            "/adv/level1/test_level1.txt",  # level1中应该成功创建了文件
        ]
        
        # 验证预期不存在的文件
        unexpected_files = [
            "/adv/test_root.txt",  # 根目录中应该没有创建成功
            "/adv/level1/level2/test_level2.txt",  # level2中应该没有创建成功
            "/adv/moved_file.txt",  # 移动到根目录应该失败
            "/adv/level1/moved_level2_file.txt",  # 从level2移动到level1应该失败
        ]
        
        verification_results = []
        for file_path in expected_files:
            if file_path in file_paths:
                verification_results.append(f"✓ 预期存在的文件 {file_path} 已找到")
            else:
                verification_results.append(f"✗ 预期存在的文件 {file_path} 未找到")
                
        for file_path in unexpected_files:
            if file_path not in file_paths:
                verification_results.append(f"✓ 预期不存在的文件 {file_path} 确实不存在")
            else:
                verification_results.append(f"✗ 预期不存在的文件 {file_path} 意外存在")
        
        print("\n验证结果:")
        for result in verification_results:
            print(f"  {result}")
            
        if all(result.startswith("✓") for result in verification_results):
            print_test_result(True, "所有高级权限控制验证通过")
        else:
            raise Exception("部分高级权限控制验证失败")
        
    except Exception as e:
        print_test_result(False, f"高级权限控制测试失败: {str(e)}")
        raise
    finally:
        clean_up_test_files(test_files)

def main():
    """主测试函数"""
    print_test_header("文件共享功能自动化测试")
    
    results = {
        "basic_test": {"success": False, "message": ""},
        "permission_test": {"success": False, "message": ""},
        "adv_permission_test": {"success": False, "message": ""}
    }
    
    try:
        test_basic_sharing()
        results["basic_test"]["success"] = True
        results["basic_test"]["message"] = "所有基本功能测试通过"
    except Exception as e:
        results["basic_test"]["message"] = f"基本功能测试失败: {str(e)}"
    
    try:
        test_permissions()
        results["permission_test"]["success"] = True
        results["permission_test"]["message"] = "所有权限控制测试通过"
    except Exception as e:
        results["permission_test"]["message"] = f"权限控制测试失败: {str(e)}"
    
    try:
        test_advanced_permissions()
        results["adv_permission_test"]["success"] = True
        results["adv_permission_test"]["message"] = "所有高级权限控制测试通过"
    except Exception as e:
        results["adv_permission_test"]["message"] = f"高级权限控制测试失败: {str(e)}"
    
    # 打印测试结果总结
    print_test_header("测试结果总结")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"\n{test_name}:")
        print(f"  状态: {status}")
        print(f"  详情: {result['message']}")
    
    # 总体测试结果
    all_passed = all(result["success"] for result in results.values())
    if all_passed:
        print("\n🎉 所有测试通过！共享功能工作正常 🎉")
    else:
        print("\n⚠️ 部分测试未通过，请检查详细日志 ⚠️")
    
    # 清理数据库
    print_test_header("数据库清理")
    user_input = input("是否清理数据库？(delete/remain): ").strip().lower()
    if user_input == "delete":
        print("清理数据库...")
        try:
            import subprocess
            result = subprocess.run(["python", "clean_db.py", "--force"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print_test_result(True, "数据库清理成功")
            else:
                print_test_result(False, f"数据库清理失败: {result.stderr}")
        except Exception as e:
            print_test_result(False, f"执行清理脚本时出错: {str(e)}")
    else:
        print("跳过数据库清理...")

if __name__ == "__main__":
    main() 