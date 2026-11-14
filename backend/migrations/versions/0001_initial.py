"""Initial application schema."""
from alembic import op
from app.database import Base
from app import models
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
def downgrade():
    bind = op.get_bind()
    # The users and saved_stocks tables predate this application and must be preserved.
    for table in (models.ResearchReport.__table__, models.ResearchTask.__table__, models.SavedStockMetadata.__table__, models.GoogleIdentity.__table__, models.UserPreference.__table__):
        table.drop(bind=bind, checkfirst=True)
