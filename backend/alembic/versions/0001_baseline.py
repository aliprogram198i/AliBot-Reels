from alembic import op
import sqlalchemy as sa
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("google_sub",sa.String(255),nullable=True), sa.Column("telegram_id",sa.Integer(),nullable=True), sa.Column("email",sa.String(320),nullable=False), sa.Column("name",sa.String(255),nullable=True), sa.Column("picture",sa.String(1000),nullable=True), sa.Column("age_eligible",sa.Boolean(),nullable=False,server_default=sa.false()), sa.Column("onboarding_complete",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.create_index("ix_users_google_sub","users",["google_sub"],unique=True)
    op.create_index("ix_users_telegram_id","users",["telegram_id"],unique=True)
    op.create_index("ix_users_email","users",["email"])
    op.create_table("user_preferences", sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),primary_key=True), sa.Column("category",sa.String(50),nullable=False))
    op.create_index("ix_user_preferences_category","user_preferences",["category"])
    op.create_table("user_country_preferences", sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),primary_key=True), sa.Column("country_code",sa.String(2),primary_key=True))
    op.create_index("ix_user_country_preferences_country_code","user_country_preferences",["country_code"])
    op.create_table("reels", sa.Column("id",sa.String(100),primary_key=True), sa.Column("category",sa.String(50),nullable=False), sa.Column("video_url",sa.String(2000),nullable=False), sa.Column("thumbnail_url",sa.String(2000),nullable=True), sa.Column("title",sa.String(500),nullable=True), sa.Column("is_adult",sa.Boolean(),nullable=False,server_default=sa.false()), sa.Column("published",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.create_index("ix_reels_category","reels",["category"]); op.create_index("ix_reels_is_adult","reels",["is_adult"]); op.create_index("ix_reels_published","reels",["published"])
    op.create_table("reel_countries", sa.Column("reel_id",sa.String(100),sa.ForeignKey("reels.id",ondelete="CASCADE"),primary_key=True), sa.Column("country_code",sa.String(2),primary_key=True))
    op.create_index("ix_reel_countries_country_code","reel_countries",["country_code"])

def downgrade():
    op.drop_index("ix_reel_countries_country_code",table_name="reel_countries"); op.drop_table("reel_countries")
    op.drop_index("ix_reels_published",table_name="reels"); op.drop_index("ix_reels_is_adult",table_name="reels"); op.drop_index("ix_reels_category",table_name="reels"); op.drop_table("reels")
    op.drop_index("ix_user_country_preferences_country_code",table_name="user_country_preferences"); op.drop_table("user_country_preferences")
    op.drop_index("ix_user_preferences_category",table_name="user_preferences"); op.drop_table("user_preferences")
    op.drop_index("ix_users_email",table_name="users"); op.drop_index("ix_users_telegram_id",table_name="users"); op.drop_index("ix_users_google_sub",table_name="users"); op.drop_table("users")
