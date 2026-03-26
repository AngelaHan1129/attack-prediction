# alembic/env.py 頂部
from app.database.session import Base
from app.models.user import User  # 必須引入具體模型
target_metadata = Base.metadata