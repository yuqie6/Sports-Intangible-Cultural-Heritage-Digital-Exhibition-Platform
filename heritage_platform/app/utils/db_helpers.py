from sqlalchemy import inspect, text
from flask import current_app
from app import db

def ensure_column_exists(table_name, column_name, column_type="TEXT"):
    """
    确保指定的表中存在指定的列，如果不存在则添加它
    
    Args:
        table_name: 表名
        column_name: 列名
        column_type: 列的数据类型
        
    Returns:
        bool: 列是否已存在或成功添加
    """
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
