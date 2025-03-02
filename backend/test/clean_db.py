#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库清理工具 - 用于清空测试数据

此脚本用于清空数据库中的测试数据和存储目录中的文件，
可选择保留特定的用户账户。

使用方法:
    - 普通模式: python clean_db.py
    - 快速模式: python clean_db.py --force
    - 保留管理员: python clean_db.py --keep-admin
    - 帮助: python clean_db.py --help
"""

import os
import sys
import argparse
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_ENGINE = "postgresql"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "123456"
DATABASE_HOST = "localhost"
DATABASE_PORT = "5432"
DATABASE_NAME = "ide"

# 数据库连接 URL
DATABASE_URL = f"{DATABASE_ENGINE}://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# 创建引擎和会话
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# 要清空的表列表（按照依赖关系顺序排列）
TABLES_TO_CLEAN = [
    "shared_entry_users",  # 首先清除用户共享关系
    "shared_entries",      # 然后清除共享条目
    "entries",             # 然后清除文件条目
    "users"                # 最后清除用户
]

# 存储路径
STORAGE_PATH = os.path.join(os.path.dirname(__file__), "storage")


def get_table_counts():
    """获取各表中的记录数"""
    counts = {}
    try:
        with Session() as session:
            for table in TABLES_TO_CLEAN:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    counts[table] = count
                except Exception as e:
                    counts[table] = f"错误: {str(e)}"
    except Exception as e:
        print(f"连接数据库时出错: {str(e)}")
        return {}
    
    return counts


def get_all_users():
    """获取所有用户信息"""
    users = []
    try:
        with Session() as session:
            try:
                result = session.execute(text("SELECT id, username, role FROM users"))
                for row in result:
                    users.append({
                        "id": row[0],
                        "username": row[1],
                        "role": row[2]
                    })
            except Exception as e:
                print(f"获取用户信息时出错: {str(e)}")
    except Exception as e:
        print(f"连接数据库时出错: {str(e)}")
    
    return users


def get_admin_users():
    """获取所有管理员用户ID"""
    admin_ids = []
    try:
        with Session() as session:
            try:
                result = session.execute(text("SELECT id FROM users WHERE role = 'admin'"))
                admin_ids = [row[0] for row in result]
            except Exception as e:
                print(f"获取管理员用户时出错: {str(e)}")
    except Exception as e:
        print(f"连接数据库时出错: {str(e)}")
    
    return admin_ids


def reset_sequences():
    """重置所有序列"""
    try:
        with Session() as session:
            # 查询所有带有序列的表和列
            query = """
            SELECT 
                pg_get_serial_sequence('"' || table_name || '"', column_name) as sequence_name
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'public'
                AND column_default LIKE 'nextval%'
            """
            result = session.execute(text(query))
            sequences = [row[0] for row in result if row[0] is not None]
            
            # 重置所有序列到1
            for sequence in sequences:
                session.execute(text(f"ALTER SEQUENCE {sequence} RESTART WITH 1"))
            
            session.commit()
            print(f"已重置 {len(sequences)} 个序列")
    except Exception as e:
        print(f"重置序列时出错: {str(e)}")


def clean_tables(preserve_user_ids=None):
    """清空指定的数据库表，可选择保留特定用户"""
    if preserve_user_ids is None:
        preserve_user_ids = []
    
    try:
        with Session() as session:
            # 关闭外键约束检查
            session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            
            # 特殊处理users表，如果有需要保留的用户
            tables_to_clean = list(TABLES_TO_CLEAN)  # 创建副本以便修改
            
            if preserve_user_ids and "users" in tables_to_clean:
                try:
                    user_ids_str = ", ".join([str(uid) for uid in preserve_user_ids])
                    result = session.execute(text(f"DELETE FROM users WHERE id NOT IN ({user_ids_str})"))
                    print(f"已清空users表，删除了 {result.rowcount if hasattr(result, 'rowcount') else '?'} 行，保留 {len(preserve_user_ids)} 个用户")
                    tables_to_clean.remove("users")  # 从待清空列表中移除users表
                except Exception as e:
                    print(f"清空表 users 时出错: {str(e)}")
            
            # 清空其他表
            for table in tables_to_clean:
                try:
                    result = session.execute(text(f"DELETE FROM {table}"))
                    print(f"已清空表 {table}，删除了 {result.rowcount if hasattr(result, 'rowcount') else '?'} 行")
                except Exception as e:
                    print(f"清空表 {table} 时出错: {str(e)}")
            
            # 提交事务
            session.commit()
            print("所有表已清空")
    except Exception as e:
        print(f"清空表时出错: {str(e)}")


def clean_storage():
    """清空存储目录中的文件，但保留目录结构"""
    if not os.path.exists(STORAGE_PATH):
        print(f"存储目录 {STORAGE_PATH} 不存在")
        return
    
    file_count = 0
    for root, dirs, files in os.walk(STORAGE_PATH):
        for file in files:
            try:
                os.remove(os.path.join(root, file))
                file_count += 1
            except Exception as e:
                print(f"删除文件 {os.path.join(root, file)} 时出错: {str(e)}")
    
    print(f"存储目录已清空，删除了 {file_count} 个文件")


def get_confirmation():
    """获取用户确认"""
    print("\n⚠️  警告：此操作将清空数据库中的所有数据和存储文件！⚠️")
    print("此操作不可恢复，请慎重操作。")
    
    while True:
        answer = input("\n请输入 'yes' 确认清空数据库，或输入 'no' 取消操作: ").strip().lower()
        if answer == 'yes':
            return True
        elif answer == 'no':
            return False
        else:
            print("无效的输入，请输入 'yes' 或 'no'")


def select_users_to_preserve(users):
    """让用户选择要保留的账户"""
    if not users:
        print("数据库中没有用户账户")
        return []
    
    print("\n现有用户账户:")
    for i, user in enumerate(users, 1):
        print(f"  {i}. ID: {user['id']}, 用户名: {user['username']}, 角色: {user['role']}")
    
    print("\n是否保留一些用户账户？保留的账户数据将不会被删除。")
    while True:
        answer = input("请输入要保留的用户编号(多个用逗号分隔)，或输入'none'不保留任何用户: ").strip().lower()
        if answer == 'none':
            return []
        
        try:
            selected_indices = [int(idx.strip()) for idx in answer.split(',') if idx.strip()]
            if all(1 <= idx <= len(users) for idx in selected_indices):
                return [users[idx-1]['id'] for idx in selected_indices]
            else:
                print(f"无效的用户编号，请输入1到{len(users)}之间的数字")
        except ValueError:
            print("无效的输入，请输入数字或'none'")


def quick_clean():
    """快速清理数据库，无需确认"""
    print("\n" + "="*50)
    print("快速清理数据库和存储")
    print("="*50)
    
    start_time = time.time()
    
    # 清空数据库表
    print("\n--- 清空数据库表 ---")
    clean_tables()
    
    # 重置序列
    print("\n--- 重置序列 ---")
    reset_sequences()
    
    # 清空存储目录
    print("\n--- 清空存储目录 ---")
    clean_storage()
    
    end_time = time.time()
    
    print("\n" + "="*50)
    print(f"数据库和存储已清空完成 (耗时: {end_time - start_time:.2f}秒)")
    print("="*50)


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="数据库清理工具")
    parser.add_argument("--force", "-f", action="store_true", help="强制清理，无需确认")
    parser.add_argument("--keep-admin", "-a", action="store_true", help="保留所有管理员账户")
    args = parser.parse_args()
    
    # 快速清理模式
    if args.force:
        # 如果需要保留管理员
        if args.keep_admin:
            admin_ids = get_admin_users()
            if admin_ids:
                print(f"保留 {len(admin_ids)} 个管理员账户")
                clean_tables(admin_ids)
                reset_sequences()
                clean_storage()
                print("\n完成清理（保留管理员账户）")
            else:
                print("未找到管理员账户，执行完全清理")
                quick_clean()
        else:
            quick_clean()
        return
    
    # 常规模式
    print("\n" + "="*50)
    print("数据库清理工具")
    print("="*50)
    
    # 获取当前表数据量
    print("\n当前数据库表记录数:")
    table_counts = get_table_counts()
    for table, count in table_counts.items():
        print(f"  - {table}: {count} 条记录")
    
    # 获取存储文件数
    file_count = 0
    if os.path.exists(STORAGE_PATH):
        for root, dirs, files in os.walk(STORAGE_PATH):
            file_count += len(files)
    print(f"  - 存储文件: {file_count} 个文件")
    
    # 自动处理"保留管理员"选项
    preserve_user_ids = []
    if args.keep_admin:
        admin_ids = get_admin_users()
        if admin_ids:
            print(f"\n将自动保留 {len(admin_ids)} 个管理员账户")
            preserve_user_ids = admin_ids
    else:
        # 获取所有用户信息
        users = get_all_users()
        preserve_user_ids = select_users_to_preserve(users)
    
    # 获取用户确认
    if not get_confirmation():
        print("\n操作已取消")
        return
    
    print("\n" + "="*50)
    print("开始清空数据库和存储")
    if preserve_user_ids:
        print(f"(保留 {len(preserve_user_ids)} 个用户账户)")
    print("="*50)
    
    start_time = time.time()
    
    # 清空数据库表
    print("\n--- 清空数据库表 ---")
    clean_tables(preserve_user_ids)
    
    # 重置序列
    print("\n--- 重置序列 ---")
    reset_sequences()
    
    # 清空存储目录
    print("\n--- 清空存储目录 ---")
    clean_storage()
    
    end_time = time.time()
    
    print("\n" + "="*50)
    print(f"数据库和存储已清空完成 (耗时: {end_time - start_time:.2f}秒)")
    print("="*50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 