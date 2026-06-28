"""Harden relational integrity and query indexes.

Revision ID: 001_relational_integrity
Revises:
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "001_relational_integrity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DELETE f
        FROM friendships AS f
        JOIN (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY LEAST(user_id, friend_id),
                                     GREATEST(user_id, friend_id)
                        ORDER BY
                            CASE status
                                WHEN 'ACCEPTED' THEN 0
                                WHEN 'PENDING' THEN 1
                                ELSE 2
                            END,
                            id DESC
                    ) AS rn
                FROM friendships
            ) AS ranked
            WHERE rn > 1
        ) AS duplicates ON duplicates.id = f.id
        """
    )
    op.execute("DELETE FROM friendships WHERE user_id = friend_id")
    op.execute("UPDATE messages SET is_read = b'0' WHERE is_read IS NULL")

    op.alter_column(
        "messages",
        "is_read",
        existing_type=mysql.BIT(1),
        nullable=False,
        server_default=sa.text("b'0'"),
    )

    op.create_index(
        "ix_messages_sender_receiver_created",
        "messages",
        ["sender_id", "receiver_id", "create_time", "id"],
    )
    op.create_index(
        "ix_messages_receiver_sender_created",
        "messages",
        ["receiver_id", "sender_id", "create_time", "id"],
    )
    op.create_index(
        "ix_messages_receiver_read_created",
        "messages",
        ["receiver_id", "is_read", "create_time", "id"],
    )
    op.create_index(
        "ix_friendships_user_status_created",
        "friendships",
        ["user_id", "status", "create_time"],
    )
    op.create_index(
        "ix_friendships_friend_status_created",
        "friendships",
        ["friend_id", "status", "create_time"],
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_friendships_pair
        ON friendships (
            (LEAST(user_id, friend_id)),
            (GREATEST(user_id, friend_id))
        )
        """
    )
    op.create_check_constraint(
        "ck_friendships_not_self",
        "friendships",
        "user_id <> friend_id",
    )

    op.create_index(
        "ix_posts_created_id",
        "posts",
        ["create_time", "id"],
    )
    op.create_index(
        "ix_posts_user_created_id",
        "posts",
        ["user_id", "create_time", "id"],
    )
    op.create_index(
        "ix_comments_post_created_id",
        "comments",
        ["post_id", "create_time", "id"],
    )
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_post_likes_user_id", "post_likes", ["user_id"])
    op.create_index(
        "uq_user_interests_user_interest",
        "user_interests",
        ["user_id", "interest"],
        unique=True,
    )

    op.create_foreign_key(
        "fk_posts_user",
        "posts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_comments_post",
        "comments",
        "posts",
        ["post_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_comments_user",
        "comments",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_post_likes_post",
        "post_likes",
        "posts",
        ["post_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_post_likes_user",
        "post_likes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_post_likes_user", "post_likes", type_="foreignkey")
    op.drop_constraint("fk_post_likes_post", "post_likes", type_="foreignkey")
    op.drop_constraint("fk_comments_user", "comments", type_="foreignkey")
    op.drop_constraint("fk_comments_post", "comments", type_="foreignkey")
    op.drop_constraint("fk_posts_user", "posts", type_="foreignkey")

    op.drop_index("uq_user_interests_user_interest", table_name="user_interests")
    op.drop_index("ix_post_likes_user_id", table_name="post_likes")
    op.drop_index("ix_comments_user_id", table_name="comments")
    op.drop_index("ix_comments_post_created_id", table_name="comments")
    op.drop_index("ix_posts_user_created_id", table_name="posts")
    op.drop_index("ix_posts_created_id", table_name="posts")
    op.drop_constraint("ck_friendships_not_self", "friendships", type_="check")
    op.execute("DROP INDEX uq_friendships_pair ON friendships")
    op.drop_index(
        "ix_friendships_friend_status_created",
        table_name="friendships",
    )
    op.drop_index(
        "ix_friendships_user_status_created",
        table_name="friendships",
    )
    op.drop_index(
        "ix_messages_receiver_read_created",
        table_name="messages",
    )
    op.drop_index(
        "ix_messages_receiver_sender_created",
        table_name="messages",
    )
    op.drop_index(
        "ix_messages_sender_receiver_created",
        table_name="messages",
    )
    op.alter_column(
        "messages",
        "is_read",
        existing_type=mysql.BIT(1),
        nullable=True,
        server_default=None,
    )
