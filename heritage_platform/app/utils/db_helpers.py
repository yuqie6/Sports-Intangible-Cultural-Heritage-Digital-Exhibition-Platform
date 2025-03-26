from sqlalchemy import inspect, text
from flask import current_app
from app import db
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

def ensure_column_exists(table_name: str, column_name: str, column_type: str = "TEXT") -> bool:
    """确保指定的表中存在指定的列，如果不存在则添加它"""
    try:
        # 检查列是否存在
        insp = inspect(db.engine)
        columns = [c['name'] for c in insp.get_columns(table_name)]
        
        if column_name in columns:
            current_app.logger.info(f"列 {column_name} 已存在于表 {table_name} 中")
            return True
            
        # 添加列
        sql = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        db.session.execute(sql)
        db.session.commit()
        
        current_app.logger.info(f"成功添加列 {column_name} 到表 {table_name}")
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加列 {column_name} 到表 {table_name} 失败: {str(e)}")
        return False

def table_exists(table_name: str) -> bool:
    """检查表是否存在
    
    Args:
        table_name: 要检查的表名
        
    Returns:
        bool: 表是否存在
    """
    try:
        insp = inspect(db.engine)
        return table_name in insp.get_table_names()
    except Exception as e:
        current_app.logger.error(f"检查表 {table_name} 是否存在时出错: {str(e)}")
        return False

def get_column_names(table_name: str) -> List[str]:
    """获取表的所有列名
    
    Args:
        table_name: 表名
        
    Returns:
        list: 列名列表
    """
    try:
        insp = inspect(db.engine)
        return [c['name'] for c in insp.get_columns(table_name)]
    except Exception as e:
        current_app.logger.error(f"获取表 {table_name} 的列名时出错: {str(e)}")
        return []

@contextmanager
def safe_db_operation():
    """数据库操作的安全上下文管理器
    
    用法:
        with safe_db_operation() as session:
            session.add(some_model)
    """
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"数据库操作失败: {str(e)}")
        raise

def execute_sql(sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """安全执行SQL语句
    
    Args:
        sql: SQL语句
        params: SQL参数字典
        
    Returns:
        执行结果
    """
    try:
        with safe_db_operation() as session:
            if params:
                result = session.execute(text(sql), params)
            else:
                result = session.execute(text(sql))
            return result
    except Exception as e:
        current_app.logger.error(f"执行SQL失败: {str(e)}, SQL: {sql}, 参数: {params}")
        raise

def batch_insert(model, items: List[Dict[str, Any]]) -> bool:
    """批量插入数据
    
    Args:
        model: SQLAlchemy模型类
        items: 要插入的数据列表
        
    Returns:
        bool: 是否成功
    """
    try:
        with safe_db_operation() as session:
            session.bulk_insert_mappings(model, items)
        return True
    except Exception as e:
        current_app.logger.error(f"批量插入数据失败: {str(e)}")
        return False
